"""Interface (contrato) do facade de produtos (catálogo)."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class facedeProdutoInterface(Protocol):
    """Operações de leitura do catálogo de produtos."""

    def listar(self) -> list[dict[str, Any]]:
        """Lista todos os produtos, ordenados por categoria e código.

        Returns:
            list[dict[str, Any]]: produtos com `id`, `codigo`, `descricao` e `categoria`.
        """
        ...
