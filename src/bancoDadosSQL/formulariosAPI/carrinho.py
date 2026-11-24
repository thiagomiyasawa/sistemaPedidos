"""Rotas do carrinho do usuário autenticado.

GET    /carrinho                    — itens do carrinho.
POST   /carrinho/itens              — adiciona um produto (soma se já estiver no carrinho).
DELETE /carrinho/itens/{produto_id} — remove um produto.
DELETE /carrinho                    — esvazia o carrinho.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field

from .validacoes import INT_MAX, Quantidade

IdProduto = Annotated[int, Path(ge=1, le=INT_MAX)]


class AdicionarCarrinhoEntrada(BaseModel):
    """Corpo de `POST /carrinho/itens`.

    Campos:
        produto_id: Produto (da tabela `produtos`) a adicionar.
        quantidade: Quantidade a somar (inteiro positivo, até o limite permitido).

    Campos extras são rejeitados (`extra="forbid"`).
    """

    model_config = ConfigDict(extra="forbid")

    produto_id: Annotated[int, Field(ge=1, le=INT_MAX)]
    quantidade: Quantidade


class ItemCarrinhoSaida(BaseModel):
    """Item do carrinho, com os dados do produto.

    Campos:
        produto_id: Identificador do produto.
        codigo: Código do produto.
        descricao: Nome/descrição do produto.
        categoria: Categoria do produto.
        quantidade: Quantidade acumulada no carrinho.
    """

    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    codigo: str | None
    descricao: str | None
    categoria: str | None
    quantidade: int


ListarCarrinhoSaida = list[ItemCarrinhoSaida]
