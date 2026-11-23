"""GET /pedidos/{pedido_id} — sem corpo de entrada (só o id na URL)."""
from __future__ import annotations

from .saidaPedido import PedidoSaida

ObterPedidoSaida = PedidoSaida