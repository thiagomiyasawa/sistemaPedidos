"""Formulários de saída compartilhados: representação de `Pedido` e `ItemPedido`."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from bancoDadosSQL.entidades.pedidos import ItemPedido, Pedido


class ItemPedidoSaida(BaseModel):
    """Representação de saída (resposta JSON) de um item de pedido.

    Campos:
        id: Identificador do item (nulo se ainda não gravado).
        id_pedido: Identificador do pedido dono do item.
        produto: Nome do produto.
        quant: Quantidade solicitada.
        data_necessidade: Data de necessidade (opcional).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int | None
    id_pedido: int | None
    produto: str
    quant: int
    data_necessidade: date | None

    def para_entidade(self) -> ItemPedido:
        """Converte a resposta JSON na entidade `ItemPedido`.

        Returns:
            `ItemPedido` com os mesmos valores dos campos deste formulário.
        """
        return ItemPedido(**self.model_dump())


class PedidoSaida(BaseModel):
    """Representação de saída (resposta JSON) de um pedido, com seus itens.

    Campos:
        id: Identificador do pedido.
        cod_rm: Código do pedido no RM (opcional).
        num_itens: Quantidade de itens do pedido.
        status_atual: Status atual.
        data_criacao: Data/hora de criação (UTC, sem fuso).
        origem: Origem do pedido.
        local_entrega: Local de entrega.
        obra: Obra do pedido.
        tarefa: Tarefa da obra.
        itens: Lista de `ItemPedidoSaida`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int | None
    cod_rm: int | None
    num_itens: int
    status_atual: str
    data_criacao: datetime | None
    origem: str
    local_entrega: str
    obra: str
    tarefa: str
    itens: list[ItemPedidoSaida]

    def para_entidade(self) -> Pedido:
        """Converte a resposta JSON (já validada) na entidade `Pedido` com seus itens.

        Returns:
            `Pedido` com os campos deste formulário e a lista de `ItemPedido` correspondente.
        """
        dados = self.model_dump(exclude={"itens"})
        return Pedido(itens=[i.para_entidade() for i in self.itens], **dados)