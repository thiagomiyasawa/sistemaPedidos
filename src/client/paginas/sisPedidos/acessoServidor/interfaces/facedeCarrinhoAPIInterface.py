"""Interface (contrato) do facade do carrinho usado pelo cliente.

O carrinho é guardado no banco, por usuário, e acessado pela API; o dono é o usuário da chave.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Protocol, Self, runtime_checkable

from client.paginas.sisPedidos.entidades.itemCarrinho import ItemCarrinho


@runtime_checkable
class facedeCarrinhoAPIInterface(Protocol):
    """Leitura e alteração do carrinho do usuário, mais o ciclo de vida."""

    def listar(self) -> list[ItemCarrinho]:
        """Itens do carrinho, na ordem de inclusão.

        Returns:
            list[ItemCarrinho]: itens do carrinho.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        ...

    def adicionar(self, produto_id: int, quant: int, uni: str,
                  data_necessidade: date) -> list[ItemCarrinho]:
        """Soma `quant` ao produto na data e unidade (cria a linha se não existir).

        O mesmo produto pode ter várias linhas, com datas ou unidades diferentes.

        Args:
            produto_id: produto a adicionar.
            quant: quantidade a somar (positiva).
            uni: unidade de medida da quantidade.
            data_necessidade: data em que o item é necessário.

        Returns:
            list[ItemCarrinho]: carrinho após a inclusão.

        Raises:
            ApiError: em falha de comunicação ou se a API recusar (ex.: produto inexistente).
        """
        ...

    def remover(self, itens_ids: Iterable[int]) -> None:
        """Remove linhas do carrinho (as que já não existem são ignoradas).

        Args:
            itens_ids: ids das linhas (`ItemCarrinho.id`) a remover.

        Returns:
            None.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        ...

    def finalizar(self, obra: str, tarefa: str, local_entrega: str) -> int:
        """Fecha o carrinho: o servidor monta o pedido com as linhas dele e o esvazia.

        Args:
            obra: obra do pedido.
            tarefa: tarefa da obra.
            local_entrega: local de entrega.

        Returns:
            int: número (id) do pedido criado.

        Raises:
            ApiError: em falha de comunicação ou se a API recusar (ex.: carrinho vazio).
        """
        ...

    def limpar(self) -> None:
        """Esvazia o carrinho.

        Returns:
            None.

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
