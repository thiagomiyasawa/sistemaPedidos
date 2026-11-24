"""Facade do carrinho: itens que o usuário separou para o pedido (`carrinho_itens_cadastro`).

Depende apenas de `dbAdapterInterface`.

Uso:
    with DIC.db() as db:
        itens = FacedeCarrinho(db).listar(user_id=1)
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..dbAdapterInterface import dbAdapterInterface
from .interfaces.facedeCarrinhoInterface import facedeCarrinhoInterface


class FacedeCarrinho(facedeCarrinhoInterface):
    """Implementação SQL do carrinho por usuário.

    Attributes:
        db: adapter de banco usado para executar as consultas.
    """

    def __init__(self, db: dbAdapterInterface) -> None:
        """Inicializa o facade com o adapter de banco.

        Args:
            db: adapter que satisfaz `dbAdapterInterface`.
        """
        self.db = db

    def listar(self, user_id: int) -> list[dict[str, Any]]:
        """Itens do carrinho, na ordem de inclusão, com os dados do produto.

        Args:
            user_id: dono do carrinho.

        Returns:
            list[dict[str, Any]]: itens com `produto_id`, `codigo`, `descricao`, `categoria`
            e `quantidade`.
        """
        linhas = self.db.fetch_all(
            "SELECT c.produto_id, p.codigo, p.descricao, p.categoria, c.quantidade "
            "FROM carrinho_itens_cadastro c JOIN produtos p ON p.id = c.produto_id "
            "WHERE c.user_id = ? ORDER BY c.rowid",
            (user_id,),
        )
        return [dict(linha) for linha in linhas]

    def adicionar(self, user_id: int, produto_id: int, quantidade: int) -> bool:
        """Soma `quantidade` ao produto no carrinho (cria o item se não existir).

        Args:
            user_id: dono do carrinho.
            produto_id: produto a adicionar.
            quantidade: quantidade a somar (positiva).

        Returns:
            bool: True se adicionou; False se o produto não existir.
        """
        cur = self.db.execute(
            "INSERT INTO carrinho_itens_cadastro (user_id, produto_id, quantidade) "
            "SELECT ?, id, ? FROM produtos WHERE id = ? "
            "ON CONFLICT(user_id, produto_id) DO UPDATE SET quantidade = quantidade + excluded.quantidade",
            (user_id, quantidade, produto_id),
        )
        return cur.rowcount > 0

    def remover(self, user_id: int, produtos_ids: Iterable[int]) -> int:
        """Remove produtos do carrinho (ids que não estão nele são ignorados).

        Args:
            user_id: dono do carrinho.
            produtos_ids: produtos a remover.

        Returns:
            int: quantos itens foram removidos.
        """
        ids = list(produtos_ids)
        if not ids:
            return 0
        marcas = ",".join("?" * len(ids))
        cur = self.db.execute(
            f"DELETE FROM carrinho_itens_cadastro WHERE user_id = ? AND produto_id IN ({marcas})",
            (user_id, *ids),
        )
        return cur.rowcount

    def limpar(self, user_id: int) -> None:
        """Esvazia o carrinho do usuário.

        Args:
            user_id: dono do carrinho.

        Returns:
            None.
        """
        self.db.execute("DELETE FROM carrinho_itens_cadastro WHERE user_id = ?", (user_id,))
