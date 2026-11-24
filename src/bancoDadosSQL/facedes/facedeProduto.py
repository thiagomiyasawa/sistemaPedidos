"""Facade de produtos: leitura do catálogo (tabela `produtos`).

Depende apenas de `dbAdapterInterface`.

Uso:
    with DIC.db() as db:
        produtos = FacedeProduto(db).listar()
"""
from __future__ import annotations

from typing import Any

from ..dbAdapterInterface import dbAdapterInterface
from .interfaces.facedeProdutoInterface import facedeProdutoInterface


class FacedeProduto(facedeProdutoInterface):
    """Implementação SQL da leitura do catálogo de produtos.

    Attributes:
        db: adapter de banco usado para executar as consultas.
    """

    def __init__(self, db: dbAdapterInterface) -> None:
        """Inicializa o facade com o adapter de banco.

        Args:
            db: adapter que satisfaz `dbAdapterInterface`.
        """
        self.db = db

    def listar(self) -> list[dict[str, Any]]:
        """Lista todos os produtos, ordenados por categoria e código.

        Returns:
            list[dict[str, Any]]: produtos com `id`, `codigo`, `descricao` e `categoria`.
        """
        linhas = self.db.fetch_all(
            "SELECT id, codigo, descricao, categoria FROM produtos "
            "ORDER BY categoria, codigo, id"
        )
        return [dict(l) for l in linhas]
