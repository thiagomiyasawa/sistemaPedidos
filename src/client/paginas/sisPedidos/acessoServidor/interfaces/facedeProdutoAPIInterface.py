"""Interface (contrato) do facade de produtos usado pelo cliente."""
from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from client.paginas.sisPedidos.entidades.produto import Produto


@runtime_checkable
class facedeProdutoAPIInterface(Protocol):
    """Leitura do catálogo de produtos, mais o ciclo de vida."""

    def listar(self) -> list[Produto]:
        """Lista os produtos do catálogo, ordenados por categoria e código.

        Returns:
            list[Produto]: produtos do catálogo.

        Raises:
            ApiError: em falha de comunicação com a API.
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
