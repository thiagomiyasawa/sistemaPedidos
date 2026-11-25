"""GET /pedidos — filtros e paginação (query string) e lista de pedidos."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .saidaPedido import PedidoSaida
from .validacoes import INT_MAX, Obra, Status


class ListarPedidosEntrada(BaseModel):
    """Filtros e paginação (query string) de `GET /pedidos`.

    Campos:
        obra: Filtra por obra (opcional).
        status_atual: Filtra por status (opcional).
        ordem: "asc" (padrão, do mais antigo) ou "desc" (do mais novo) por número do pedido.
        apenas_meus: Se True, só os pedidos do usuário autenticado, mesmo que ele possa ver os
            de todos (padrão False).
        limit: Máximo de pedidos retornados (1 a 1000; padrão 100).
        offset: Quantidade de pedidos a pular (0 até `INT_MAX`; padrão 0).

    O total de pedidos que casam com o filtro vai no cabeçalho `X-Total-Count` da resposta.
    """

    model_config = ConfigDict(extra="forbid")  # parâmetros desconhecidos → 422

    obra: Obra | None = None
    status_atual: Status | None = None
    ordem: Literal["asc", "desc"] = "asc"
    apenas_meus: bool = False
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0, le=INT_MAX)


ListarPedidosSaida = list[PedidoSaida]