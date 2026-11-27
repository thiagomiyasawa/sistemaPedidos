"""Facade de autenticação sobre a API HTTP.

`FacedeAutenticacaoAPI` fala com `POST /login` pelo `adapterAPIInterface` (injetado; por
padrão `AdapterAPI`). Após o login, grava a chave no próprio adapter, de modo que todos os
facades que compartilham esse adapter (ver `DIC.api`) passam a enviar `X-API-Key`, e guarda
chave e validade no armazenamento de sessão (por padrão, um arquivo local).

Uso:
    with FacedeAutenticacaoAPI() as auth:
        sessao = auth.login("maria", "senha-secreta")  # None se credenciais inválidas
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Self

from client.adapters.adapterAPI import AdapterAPI
from client.adapters.interfaces.adapterAPIInterface import ApiError, adapterAPIInterface
from client.armazenamento.interfaces.armazenamentoSessaoInterface import (
    armazenamentoSessaoInterface,
)
from client.armazenamento.sessaoArquivo import SessaoArquivo
from client.facedes.interfaces.facedeAutenticacaoInterface import (
    Sessao,
    facedeAutenticacaoInterface,
)

log = logging.getLogger(__name__)


class FacedeAutenticacaoAPI(facedeAutenticacaoInterface):
    """Facade de autenticação que consome os endpoints de login da API HTTP.

    Atributos:
        api: adapter de transporte usado nas requisições.
        armazenamento: onde a sessão (chave e validade) é guardada após o login.
    """

    def __init__(self, api: adapterAPIInterface | None = None,
                 armazenamento: armazenamentoSessaoInterface | None = None) -> None:
        """Inicializa o facade.

        Args:
            api: adapter HTTP a usar; se None cria um `AdapterAPI` padrão.
            armazenamento: guarda a sessão; se None usa `SessaoArquivo()` (arquivo local).
        """
        self.api: adapterAPIInterface = api or AdapterAPI()
        self.armazenamento: armazenamentoSessaoInterface = armazenamento or SessaoArquivo()

    # --- ciclo de vida: fecha o adapter ------------------------------------
    def close(self) -> None:
        """Fecha o adapter e libera a conexão.

        Returns:
            None.
        """
        self.api.close()

    def __enter__(self) -> Self:
        """Entra no contexto `with`.

        Returns:
            O próprio facade.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o facade.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None (exceções não são suprimidas).
        """
        self.close()

    # --- autenticação ------------------------------------------------------
    def login(self, nome: str, senha: str) -> Sessao | None:
        """Chama `POST /login`; se aceito, passa o adapter a enviar a chave e guarda a sessão.

        Falha ao gravar o arquivo não invalida o login: é só registrada no log.

        Args:
            nome: nome do usuário.
            senha: senha do usuário.

        Returns:
            Sessao | None: a sessão, ou None se a API responder 401.

        Raises:
            ApiError: em falha de rede, timeout ou erro da API diferente de 401.
        """
        try:
            resp = self.api.post("/login", json={"nome": nome, "senha": senha})
        except ApiError as e:
            if e.status_code == 401:
                return None
            raise
        self.api.definir_api_key(resp["chave"])
        sessao = Sessao(chave=resp["chave"], expira_em=resp["expira_em"])
        try:
            self.armazenamento.salvar(sessao)
        except OSError:
            log.warning("Não foi possível gravar a sessão em arquivo", exc_info=True)
        return sessao

    def logout(self) -> bool:
        """Chama `POST /logout` e, aconteça o que acontecer, esquece a sessão localmente.

        O servidor apaga a chave, o que encerra a sessão em todos os computadores que a
        compartilham. Um 401 (chave já vencida ou revogada) conta como sucesso. Qualquer outra
        falha é só registrada no log: o usuário sai do app mesmo assim.

        Returns:
            bool: True se a API revogou a chave (ou ela já era inválida); False se não foi
            possível avisar a API.
        """
        revogada = True
        try:
            self.api.post("/logout")
        except ApiError as e:
            revogada = e.status_code == 401
            if not revogada:
                log.warning("Não foi possível revogar a chave na API: %s", e)
        self.api.definir_api_key("")
        try:
            self.armazenamento.limpar()
        except OSError:
            log.warning("Não foi possível apagar a sessão guardada", exc_info=True)
        return revogada

    def restaurar_sessao(self) -> Sessao | None:
        """Reaproveita a sessão guardada: confere o vencimento e pergunta à API se a chave vale.

        A conferência na API (`GET /health`, que exige chave) cobre chave revogada ou usuário
        desativado. Sessão vencida ou recusada (401) é apagada do armazenamento; se a API estiver
        inacessível a sessão é mantida, mas não restaurada.

        Returns:
            Sessao | None: a sessão restaurada, ou None se não houver sessão utilizável.
        """
        sessao = self.armazenamento.carregar()
        if sessao is None:
            return None
        try:
            vencimento = datetime.fromisoformat(sessao.expira_em)
        except ValueError:
            self.armazenamento.limpar()
            return None
        if vencimento.tzinfo is None:  # a API devolve UTC
            vencimento = vencimento.replace(tzinfo=UTC)
        if vencimento <= datetime.now(UTC):
            self.armazenamento.limpar()
            return None
        self.api.definir_api_key(sessao.chave)
        try:
            self.api.get("/health")
        except ApiError as e:
            self.api.definir_api_key("")
            if e.status_code == 401:
                self.armazenamento.limpar()
            return None
        return sessao
