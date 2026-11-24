"""Interface (contrato) do facade do carrinho (tabela `carrinho_itens_cadastro`).

O carrinho é do usuário: toda operação recebe o `user_id` dono do carrinho.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class facedeCarrinhoInterface(Protocol):
    """Leitura e alteração do carrinho de um usuário."""

    def listar(self, user_id: int) -> list[dict[str, Any]]:
        """Itens do carrinho, na ordem de inclusão, com os dados do produto.

        Args:
            user_id: dono do carrinho.

        Returns:
            list[dict[str, Any]]: itens com `produto_id`, `codigo`, `descricao`, `categoria`
            e `quantidade`.
        """
        ...

    def adicionar(self, user_id: int, produto_id: int, quantidade: int) -> bool:
        """Soma `quantidade` ao produto no carrinho (cria o item se não existir).

        Args:
            user_id: dono do carrinho.
            produto_id: produto a adicionar.
            quantidade: quantidade a somar (positiva).

        Returns:
            bool: True se adicionou; False se o produto não existir.
        """
        ...

    def remover(self, user_id: int, produtos_ids: Iterable[int]) -> int:
        """Remove produtos do carrinho (ids que não estão nele são ignorados).

        Args:
            user_id: dono do carrinho.
            produtos_ids: produtos a remover.

        Returns:
            int: quantos itens foram removidos.
        """
        ...

    def limpar(self, user_id: int) -> None:
        """Esvazia o carrinho do usuário.

        Args:
            user_id: dono do carrinho.

        Returns:
            None.
        """
        ...
