"""Rotas do carrinho do usuário autenticado.

GET    /carrinho                 — itens do carrinho.
POST   /carrinho/finalizar        — cria o pedido com os itens do carrinho e esvazia o carrinho.
POST   /carrinho/itens           — adiciona um produto numa data de necessidade e unidade (soma
                                   se já houver o mesmo produto, data e unidade).
DELETE /carrinho/itens/{item_id} — remove um item (uma linha do carrinho).
DELETE /carrinho                 — esvazia o carrinho.

O mesmo produto pode aparecer em várias linhas, desde que com data de necessidade ou unidade
diferentes.
"""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field

from .validacoes import (INT_MAX, DataNecessidade, LocalEntrega, Obra, Quantidade, Tarefa,
                         Unidade)

IdItemCarrinho = Annotated[int, Path(ge=1, le=INT_MAX)]


class AdicionarCarrinhoEntrada(BaseModel):
    """Corpo de `POST /carrinho/itens`.

    Campos:
        produto_id: Produto (da tabela `produtos`) a adicionar.
        quantidade: Quantidade a somar (inteiro positivo, até o limite permitido).
        unidade: Unidade de medida da quantidade (obrigatória).
        data_necessidade: Data em que o item é necessário (obrigatória; deve ser plausível).

    Campos extras são rejeitados (`extra="forbid"`).
    """

    model_config = ConfigDict(extra="forbid")

    produto_id: Annotated[int, Field(ge=1, le=INT_MAX)]
    quantidade: Quantidade
    unidade: Unidade
    data_necessidade: DataNecessidade


class FinalizarCarrinhoEntrada(BaseModel):
    """Corpo de `POST /carrinho/finalizar`: os dados do pedido que o carrinho não tem.

    Campos:
        obra: Obra do pedido.
        tarefa: Tarefa da obra.
        local_entrega: Local de entrega.

    Campos extras são rejeitados (`extra="forbid"`).
    """

    model_config = ConfigDict(extra="forbid")

    obra: Obra
    tarefa: Tarefa
    local_entrega: LocalEntrega


class ItemCarrinhoSaida(BaseModel):
    """Item (linha) do carrinho, com os dados do produto.

    Campos:
        id: Identificador da linha do carrinho (usado para removê-la).
        produto_id: Identificador do produto.
        codigo: Código do produto.
        descricao: Nome/descrição do produto.
        categoria: Categoria do produto.
        quantidade: Quantidade acumulada no carrinho.
        unidade: Unidade de medida da quantidade.
        data_necessidade: Data de necessidade do item.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    codigo: str | None
    descricao: str | None
    categoria: str | None
    quantidade: int
    unidade: str
    data_necessidade: date


ListarCarrinhoSaida = list[ItemCarrinhoSaida]
