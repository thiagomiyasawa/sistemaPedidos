"""Interface (contrato) do facade de autenticação usado pelo cliente.

Qualquer implementação (HTTP real, fake para testes, ...) pode ser trocada no `DIC` sem
alterar quem a usa (a página de login).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Self, runtime_checkable


@dataclass(frozen=True)
class Sessao:
    """Resultado de um login bem-sucedido.

    Atributos:
        chave: chave de API emitida (enviada em `X-API-Key`).
        expira_em: instante de vencimento da chave (UTC, texto ISO 8601).
    """

    chave: str
    expira_em: str


@runtime_checkable
class facedeAutenticacaoInterface(Protocol):
    """Login do usuário, mais o ciclo de vida."""

    def login(self, nome: str, senha: str) -> Sessao | None:
        """Troca nome e senha por uma chave de API e a passa a usar nas próximas requisições.

        Args:
            nome: nome do usuário.
            senha: senha do usuário.

        Returns:
            Sessao | None: a sessão, ou None se usuário ou senha estiverem incorretos.

        Raises:
            ApiError: em falha de rede, timeout ou erro da API diferente de credencial inválida.
        """
        ...

    def restaurar_sessao(self) -> Sessao | None:
        """Reaproveita a sessão guardada, se ainda valer, e passa a usá-la nas requisições.

        Descarta a sessão guardada quando vencida ou recusada pela API (401).

        Returns:
            Sessao | None: a sessão restaurada, ou None se não houver sessão válida (ou se a
            API não puder ser consultada no momento).
        """
        ...

    def logout(self) -> bool:
        """Encerra a sessão: revoga a chave na API e esquece a sessão neste computador.

        O lado local é sempre limpo (a chave deixa de ser enviada e a sessão guardada é
        apagada), mesmo que a API não responda.

        Returns:
            bool: True se a API revogou a chave (ou ela já era inválida); False se não foi
            possível avisar a API (a chave continua valendo no servidor até vencer).
        """
        ...

    def close(self) -> None:
        """Libera a conexão/recursos.

        Returns:
            None.
        """
        ...

    def __enter__(self) -> Self:
        """Entra no contexto `with`."""
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o facade."""
        ...
