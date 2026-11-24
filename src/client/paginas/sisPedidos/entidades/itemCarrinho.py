"""Entidade `ItemCarrinho`: um produto e a quantidade acumulada no carrinho."""
from __future__ import annotations

from dataclasses import dataclass

from client.paginas.sisPedidos.entidades.produto import Produto


@dataclass
class ItemCarrinho:
    """Item no carrinho.

    Attributes:
        produto: Produto escolhido.
        quant: Quantidade acumulada.
    """

    produto: Produto
    quant: int
