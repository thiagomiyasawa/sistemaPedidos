"""Interface (contrato) do facade do carrinho (tabela `carrinho_itens_cadastro`).

O carrinho é do usuário: toda operação recebe o `user_id` dono do carrinho. Uma linha do carrinho
é um produto numa data de necessidade e unidade: o mesmo produto pode ter várias linhas, com
datas ou unidades diferentes.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class facedeCarrinhoInterface(Protocol):
    """Leitura e alteração do carrinho de um usuário."""

    def listar(self, user_id: int) -> list[dict[str, Any]]:
        """Itens do carrinho, na ordem de inclusão, com os dados do produto.

        Args:
            user_id: dono do carrinho.

        Returns:
            list[dict[str, Any]]: itens com `id` (da linha), `produto_id`, `codigo`, `descricao`,
            `categoria`, `quantidade`, `unidade` e `data_necessidade` (texto ISO).
        """
        ...

    def adicionar(self, user_id: int, produto_id: int, quantidade: int, unidade: str,
                  data_necessidade: date) -> bool:
        """Soma `quantidade` ao produto na data e unidade (cria a linha se não existir).

        Args:
            user_id: dono do carrinho.
            produto_id: produto a adicionar.
            quantidade: quantidade a somar (positiva).
            unidade: unidade de medida da quantidade.
            data_necessidade: data em que o item é necessário.

        Returns:
            bool: True se adicionou; False se o produto não existir.
        """
        ...

    def remover(self, user_id: int, itens_ids: Iterable[int]) -> int:
        """Remove linhas do carrinho (ids que não são do usuário ou não existem são ignorados).

        Args:
            user_id: dono do carrinho.
            itens_ids: ids das linhas a remover.

        Returns:
            int: quantas linhas foram removidas.
        """
        ...

    def finalizar(self, user_id: int, obra: str, tarefa: str, local_entrega: str) -> int:
        """Cria o pedido do usuário com as linhas do carrinho e esvazia o carrinho.

        Tudo em uma única transação: se algo falhar, o pedido não é criado e o carrinho fica
        como estava.

        Args:
            user_id: dono do carrinho (e do pedido criado).
            obra: obra do pedido.
            tarefa: tarefa da obra.
            local_entrega: local de entrega.

        Returns:
            int: número (id) do pedido criado.

        Raises:
            ValueError: se o carrinho estiver vazio ou os dados violarem as regras do pedido.
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
