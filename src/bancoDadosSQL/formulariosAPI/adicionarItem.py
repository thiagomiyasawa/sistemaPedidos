"""POST /pedidos/{pedido_id}/itens — item a adicionar; devolve o pedido atualizado."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..entidades.pedidos import ItemPedido, Pedido
from .saidaPedido import PedidoSaida
from .validacoes import (MAX_ITENS_POR_PEDIDO, ConflitoIntegridade, DataNecessidade,
                         Produto, Quantidade)


class AdicionarItemEntrada(BaseModel):
    """Corpo da requisição para adicionar um item a um pedido.

    Campos:
        produto: Nome do produto (texto validado, sem caracteres de controle).
        quant: Quantidade solicitada (inteiro positivo, até o limite permitido).
        data_necessidade: Data em que o item é necessário (opcional; deve ser plausível).

    Campos extras são rejeitados (`extra="forbid"`).
    """

    model_config = ConfigDict(extra="forbid")

    produto: Produto
    quant: Quantidade
    data_necessidade: DataNecessidade | None = None

    def chave(self) -> tuple[str, object]:
        """Identifica o item dentro de um pedido (produto + data, sem diferenciar maiúsculas).

        Returns:
            Tupla (produto em casefold, data_necessidade) usada para detectar duplicados.
        """
        return (self.produto.casefold(), self.data_necessidade)

    # --- verificações contra o pedido já gravado (chamar logo após receber) ---
    def verificar_limite_itens(self, pedido: Pedido) -> None:
        """O pedido não pode ultrapassar o máximo de itens.

        Args:
            pedido: Pedido já gravado, com seus itens atuais.

        Raises:
            ConflitoIntegridade: Se o pedido já possui `MAX_ITENS_POR_PEDIDO` itens.
        """
        if len(pedido.itens) >= MAX_ITENS_POR_PEDIDO:
            raise ConflitoIntegridade(
                f"Pedido já tem o máximo de {MAX_ITENS_POR_PEDIDO} itens")

    def verificar_item_duplicado(self, pedido: Pedido) -> None:
        """Não pode existir item com o mesmo produto e data de necessidade.

        Args:
            pedido: Pedido já gravado, com seus itens atuais.

        Raises:
            ConflitoIntegridade: Se já existe item com a mesma chave (produto + data).
        """
        if any((i.produto.casefold(), i.data_necessidade) == self.chave()
               for i in pedido.itens):
            raise ConflitoIntegridade(
                "Item duplicado (mesmo produto e data de necessidade)")

    def verificar(self, pedido: Pedido) -> None:
        """Executa todas as verificações de integridade deste formulário.

        Args:
            pedido: Pedido já gravado, com seus itens atuais.

        Raises:
            ConflitoIntegridade: Se o limite de itens for atingido ou o item for duplicado.
        """
        self.verificar_limite_itens(pedido)
        self.verificar_item_duplicado(pedido)

    def para_entidade(self) -> ItemPedido:
        """Converte o formulário na entidade `ItemPedido`.

        Returns:
            `ItemPedido` com produto, quant e data_necessidade preenchidos.
        """
        return ItemPedido(**self.model_dump())


AdicionarItemSaida = PedidoSaida