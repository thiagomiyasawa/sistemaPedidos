"""GET /pedidos/{pedido_id}/itens — sem corpo de entrada; devolve os itens do pedido."""
from __future__ import annotations

from .saidaPedido import ItemPedidoSaida

ListarItensSaida = list[ItemPedidoSaida]