"""Interface (contrato) do facade de produtos (catálogo)."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class facedeProdutoInterface(Protocol):
    """Operações de leitura do catálogo de produtos."""

    def listar(self, busca: str | None = None, categoria: str | None = None,
               limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Uma página de produtos, ordenados por categoria e código.

        Args:
            busca: texto procurado no código ou na descrição, se informado.
            categoria: filtra por categoria exata, se informada.
            limit: máximo de produtos retornados.
            offset: quantidade de produtos a pular.

        Returns:
            list[dict[str, Any]]: produtos com `id`, `codigo`, `descricao` e `categoria`.
        """
        ...

    def contar(self, busca: str | None = None, categoria: str | None = None) -> int:
        """Quantos produtos casam com o filtro (para calcular o número de páginas).

        Args:
            busca: texto procurado no código ou na descrição, se informado.
            categoria: filtra por categoria exata, se informada.

        Returns:
            int: total de produtos que casam com o filtro.
        """
        ...

    def categorias(self) -> list[str]:
        """Categorias distintas do catálogo, em ordem alfabética.

        Returns:
            list[str]: categorias (sem valores vazios).
        """
        ...
