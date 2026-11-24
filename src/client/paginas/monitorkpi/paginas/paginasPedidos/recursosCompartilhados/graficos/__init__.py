"""Gráficos da página de pedidos: um módulo por gráfico.

Reexporta `CartaoGrafico` (classe base) e as classes concretas de gráfico
(`EvolucaoPedidos`, `PedidosPorObra`, `PedidosPorOrigem`, `PedidosPorStatus`,
`StatusPorObra`, `TopProdutos`), listadas em `__all__`.
"""

from client.paginas.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CartaoGrafico,
)
from .evolucaoPedidos import EvolucaoPedidos
from .pedidosPorObra import PedidosPorObra
from .pedidosPorOrigem import PedidosPorOrigem
from .pedidosPorStatus import PedidosPorStatus
from .statusPorObra import StatusPorObra
from .topProdutos import TopProdutos

__all__ = [
    "CartaoGrafico",
    "EvolucaoPedidos",
    "PedidosPorObra",
    "PedidosPorOrigem",
    "PedidosPorStatus",
    "StatusPorObra",
    "TopProdutos",
]
