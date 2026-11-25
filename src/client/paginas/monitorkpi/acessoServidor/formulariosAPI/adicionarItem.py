"""POST /pedidos/{pedido_id}/itens — item a adicionar; devolve o pedido atualizado."""
from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict

from bancoDadosSQL.entidades.pedidos import ItemPedido, Pedido

from .saidaPedido import PedidoSaida
from .validacoes import (MAX_ITENS_POR_PEDIDO, ConflitoIntegridade, DataNecessidade,
                         Produto, Quantidade, Unidade)


class AdicionarItemEntrada(BaseModel):
    """Corpo da requisição para adicionar um item a um pedido (lado cliente).

    Campos:
        produto: Nome do produto (texto validado, sem caracteres de controle).
        quant: Quantidade solicitada (inteiro positivo, até o limite permitido).
        uni: Unidade de medida da quantidade (obrigatória; texto validado).
        data_necessidade: Data em que o item é necessário (obrigatória; deve ser plausível).

    Campos extras são rejeitados (`extra="forbid"`).
    """

    model_config = ConfigDict(extra="forbid")

    produto: Produto
    quant: Quantidade
    uni: Unidade
    data_necessidade: DataNecessidade

    def chave(self) -> tuple[str, object]:
        """Identifica o item dentro de um pedido (produto + data + unidade; o produto sem diferenciar maiúsculas).

        Returns:
            Tupla (produto em casefold, data_necessidade, uni) usada para detectar duplicados.
        """
        return (self.produto.casefold(), self.data_necessidade, self.uni)

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
        """Não pode existir item com o mesmo produto, data de necessidade e unidade.

        Args:
            pedido: Pedido já gravado, com seus itens atuais.

        Raises:
            ConflitoIntegridade: Se já existe item com a mesma chave (produto + data + unidade).
        """
        if any((i.produto.casefold(), i.data_necessidade, i.uni) == self.chave()
               for i in pedido.itens):
            raise ConflitoIntegridade(
                "Item duplicado (mesmo produto, data de necessidade e unidade)")

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
            `ItemPedido` com produto, quant, uni e data_necessidade preenchidos.
        """
        return ItemPedido(**self.model_dump())

    @classmethod
    def de_entidade(cls, item: ItemPedido) -> Self:
        """Monta (e valida) o corpo da requisição a partir de um `ItemPedido`.

        Args:
            item: Entidade de item de pedido de origem.

        Returns:
            Nova instância do formulário com produto, quant, uni e data_necessidade do item.

        Raises:
            pydantic.ValidationError: Se os valores do item violarem as regras de validação.
        """
        return cls(produto=item.produto, quant=item.quant, uni=item.uni,
                   data_necessidade=item.data_necessidade)

    def para_json(self) -> dict[str, Any]:
        """Corpo JSON pronto para enviar (datas em ISO).

        Returns:
            Dicionário serializável em JSON com os campos do formulário.
        """
        return self.model_dump(mode="json")


AdicionarItemSaida = PedidoSaida