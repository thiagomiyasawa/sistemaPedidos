"""POST /pedidos — dados do novo pedido (opcionalmente com itens)."""
from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..entidades.pedidos import ItemPedido, Pedido
from .adicionarItem import AdicionarItemEntrada
from .saidaPedido import PedidoSaida
from .validacoes import (MAX_ITENS_POR_PEDIDO, CodRM, LocalEntrega, Obra, Origem,
                         Status, Tarefa)


class CriarPedidoEntrada(BaseModel):
    """Corpo do POST que cria um pedido, opcionalmente já com itens.

    Campos:
        cod_rm: Código do pedido no RM (opcional).
        status_atual: Status inicial do pedido.
        origem: Origem do pedido.
        local_entrega: Local de entrega.
        obra: Obra à qual o pedido pertence.
        tarefa: Tarefa da obra.
        itens: Lista de itens (`AdicionarItemEntrada`), sem duplicados e limitada
            a `MAX_ITENS_POR_PEDIDO`.
    """

    model_config = ConfigDict(extra="forbid")

    cod_rm: CodRM | None = None
    status_atual: Status
    origem: Origem
    local_entrega: LocalEntrega
    obra: Obra
    tarefa: Tarefa
    itens: list[AdicionarItemEntrada] = Field(default_factory=list,
                                               max_length=MAX_ITENS_POR_PEDIDO)

    @model_validator(mode="after")
    def _sem_itens_duplicados(self) -> Self:
        """Garante que não há itens repetidos (mesmo produto, data de necessidade e unidade).

        Returns:
            A própria instância, se válida.

        Raises:
            ValueError: Se houver itens duplicados.
        """
        chaves = [i.chave() for i in self.itens]
        if len(chaves) != len(set(chaves)):
            raise ValueError("itens duplicados (mesmo produto, data de necessidade e unidade)")
        return self

    def para_entidade(self) -> Pedido:
        """Converte o formulário na entidade `Pedido` com seus `ItemPedido`.

        Returns:
            `Pedido` novo, com `num_itens` derivado da quantidade de itens.
        """
        dados = self.model_dump(exclude={"itens"})
        itens = [ItemPedido(**i.model_dump()) for i in self.itens]
        # num_itens é sempre derivado dos itens, nunca informado pelo cliente.
        return Pedido(num_itens=len(itens), itens=itens, **dados)


CriarPedidoSaida = PedidoSaida