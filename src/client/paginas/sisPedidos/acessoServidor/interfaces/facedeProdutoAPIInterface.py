"""Interface (contrato) do facade de produtos usado pelo cliente."""
from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from client.paginas.sisPedidos.entidades.produto import Produto


@runtime_checkable
class facedeProdutoAPIInterface(Protocol):
    """Leitura do catálogo de produtos, mais o ciclo de vida."""

    def listar_pagina(self, busca: str | None = None, categoria: str | None = None,
                      limit: int = 30, offset: int = 0) -> tuple[list[Produto], int]:
        """Uma página do catálogo, já filtrada pelo servidor.

        Args:
            busca: texto procurado no código ou na descrição, se informado.
            categoria: filtra por categoria exata, se informada.
            limit: produtos por página.
            offset: quantidade de produtos a pular.

        Returns:
            tuple[list[Produto], int]: produtos da página (por categoria e código) e o total que
            casa com o filtro, somando todas as páginas.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        ...

    def categorias(self) -> list[str]:
        """Categorias distintas do catálogo, em ordem alfabética.

        Returns:
            list[str]: categorias.

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
