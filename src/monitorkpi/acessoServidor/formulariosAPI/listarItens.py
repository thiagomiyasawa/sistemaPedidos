"""GET /pedidos/{pedido_id}/itens — sem corpo de entrada; devolve os itens do pedido."""
from __future__ import annotations

from bancoDadosSQL.entidades.pedidos import ItemPedido

from .saidaPedido import ItemPedidoSaida

ListarItensSaida = list[ItemPedidoSaida]


def para_entidades(dados: list[dict]) -> list[ItemPedido]:
    """Converte a lista JSON de `GET /pedidos/{id}/itens` em entidades `ItemPedido`.

    Args:
        dados: Lista de dicionários, um por item, como devolvida pela API.

    Returns:
        Lista de `ItemPedido` na mesma ordem de `dados`.

    Raises:
        pydantic.ValidationError: Se algum dicionário não corresponder ao formato esperado.
    """
    return [ItemPedidoSaida.model_validate(d).para_entidade() for d in dados]