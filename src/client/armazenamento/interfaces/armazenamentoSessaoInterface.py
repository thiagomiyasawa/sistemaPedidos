"""Interface (contrato) do armazenamento local da sessão (chave de API e validade)."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from client.facedes.interfaces.facedeAutenticacaoInterface import Sessao


@runtime_checkable
class armazenamentoSessaoInterface(Protocol):
    """Guarda e recupera a última sessão autenticada."""

    def salvar(self, sessao: Sessao) -> None:
        """Grava a sessão, substituindo a anterior.

        Args:
            sessao: chave de API e vencimento a guardar.

        Returns:
            None.

        Raises:
            OSError: se não for possível gravar.
        """
        ...

    def carregar(self) -> Sessao | None:
        """Lê a sessão guardada.

        Returns:
            Sessao | None: a sessão, ou None se não houver ou se o conteúdo for inválido.
        """
        ...

    def limpar(self) -> None:
        """Apaga a sessão guardada (não falha se não existir).

        Returns:
            None.
        """
        ...
