"""Entidade `ItemCarrinho`: uma linha do carrinho (produto, quantidade, unidade e data)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from client.entidades.produto import Produto


@dataclass
class ItemCarrinho:
    """Linha do carrinho. O mesmo produto pode ter várias, com datas de necessidade ou unidades diferentes.

    Attributes:
        produto: Produto escolhido.
        quant: Quantidade acumulada.
        uni: Unidade de medida da quantidade.
        data_necessidade: Data em que o item é necessário.
        id: Identificador da linha no carrinho (usado para removê-la).
    """

    produto: Produto
    quant: int
    uni: str
    data_necessidade: date
    id: int
