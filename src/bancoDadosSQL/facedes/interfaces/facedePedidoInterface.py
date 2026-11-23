"""Interface (contrato) do facade de pedidos.

Qualquer implementação (SQL, API externa, memória para testes...) deve
satisfazer `facedePedidoInterface`. Por ser um `Protocol`, não é necessário
herdar dela: basta implementar os métodos.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...entidades.pedidos import ItemPedido, Pedido


@runtime_checkable
class facedePedidoInterface(Protocol):
    """Operações de alto nível sobre `Pedido` e `ItemPedido`."""

    def obter(self, pedido_id: int, com_itens: bool = True) -> Pedido | None:
        """Devolve o pedido (com seus itens, se pedido) ou None se não existir.

        Args:
            pedido_id: identificador do pedido.
            com_itens: se True, carrega também os itens.

        Returns:
            Pedido | None: o pedido, ou None se não existir.
        """
        ...

    def listar(
        self,
        obra: str | None = None,
        status_atual: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Pedido]:
        """Lista pedidos, com filtros opcionais e paginação.

        Args:
            obra: filtra por obra, se informada.
            status_atual: filtra por status, se informado.
            limit: máximo de pedidos retornados.
            offset: quantidade de pedidos a pular.

        Returns:
            list[Pedido]: pedidos encontrados.
        """
        ...

    def itens_do_pedido(self, pedido_id: int) -> list[ItemPedido]:
        """Devolve os itens de um pedido.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            list[ItemPedido]: itens do pedido.
        """
        ...

    def salvar(self, pedido: Pedido) -> Pedido:
        """Insere (id None) ou atualiza o pedido; insere itens novos. Devolve o pedido salvo.

        Args:
            pedido: pedido a gravar.

        Returns:
            Pedido: o pedido salvo, com IDs preenchidos.
        """
        ...

    def remover(self, pedido_id: int) -> bool:
        """Remove o pedido e seus itens. True se o pedido existia.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            bool: True se o pedido existia e foi removido.
        """
        ...
