"""Armazenamento da sessão (chave de API e validade) em um arquivo JSON local.

Local do arquivo: variável de ambiente `MONITORKPI_SESSAO_ARQUIVO`; senão `sessao.json` na
raiz do projeto (por enquanto; depois pode ir para uma pasta do usuário).
O arquivo guarda a chave em texto puro; no Linux/macOS ele é criado só com permissão do dono.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from client.armazenamento.interfaces.armazenamentoSessaoInterface import (
    armazenamentoSessaoInterface,
)
from client.facedes.interfaces.facedeAutenticacaoInterface import Sessao

RAIZ_PROJETO = Path(__file__).resolve().parents[3]  # .../sistemaPedidos


def caminho_padrao() -> Path:
    """Caminho do arquivo de sessão (ver o docstring do módulo).

    Returns:
        Path: caminho do arquivo.
    """
    if env := os.environ.get("MONITORKPI_SESSAO_ARQUIVO"):
        return Path(env)
    return RAIZ_PROJETO / "sessao.json"


class SessaoArquivo(armazenamentoSessaoInterface):
    """Guarda a sessão num arquivo JSON `{"chave": ..., "expira_em": ...}`.

    Atributos:
        caminho: arquivo onde a sessão é gravada.
    """

    def __init__(self, caminho: Path | str | None = None) -> None:
        """Define o arquivo.

        Args:
            caminho: arquivo a usar; se None usa `caminho_padrao()`.
        """
        self.caminho = Path(caminho) if caminho else caminho_padrao()

    def salvar(self, sessao: Sessao) -> None:
        """Grava a sessão de forma atômica (arquivo temporário + substituição).

        Args:
            sessao: chave de API e vencimento a guardar.

        Returns:
            None.

        Raises:
            OSError: se a pasta ou o arquivo não puderem ser escritos.
        """
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_name(self.caminho.name + ".tmp")
        fd = os.open(temporario, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"chave": sessao.chave, "expira_em": sessao.expira_em}, f)
        os.replace(temporario, self.caminho)

    def carregar(self) -> Sessao | None:
        """Lê a sessão do arquivo.

        Returns:
            Sessao | None: a sessão, ou None se o arquivo não existir ou estiver inválido.
        """
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            return Sessao(chave=str(dados["chave"]), expira_em=str(dados["expira_em"]))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def limpar(self) -> None:
        """Apaga o arquivo da sessão, se existir.

        Returns:
            None.
        """
        self.caminho.unlink(missing_ok=True)
