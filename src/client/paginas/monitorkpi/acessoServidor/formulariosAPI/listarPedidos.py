"""GET /pedidos — filtros e paginação (query string) e lista de pedidos."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from bancoDadosSQL.entidades.pedidos import Pedido

from .saidaPedido import PedidoSaida
from .validacoes import INT_MAX, Obra, Status


class ListarPedidosEntrada(BaseModel):
    """Filtros e paginação (query string) de `GET /pedidos`.

    Campos:
        obra: Filtra por obra (opcional).
        status_atual: Filtra por status (opcional).
        ordem: "asc" (padrão, do mais antigo) ou "desc" (do mais novo) por número do pedido.
        apenas_meus: Se True, só os pedidos do usuário autenticado (padrão False).
        limit: Máximo de pedidos retornados (1 a 1000; padrão 100).
        offset: Quantidade de pedidos a pular (0 até `INT_MAX`; padrão 0).
    """

    model_config = ConfigDict(extra="forbid")  # parâmetros desconhecidos → 422

    obra: Obra | None = None
    status_atual: Status | None = None
    ordem: Literal["asc", "desc"] = "asc"
    apenas_meus: bool = False
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0, le=INT_MAX)


    def params(self) -> dict:
        """Parâmetros da query string (sem os não informados).

        Returns:
            Dicionário com os campos diferentes de `None`.
        """
        return self.model_dump(exclude_none=True)


ListarPedidosSaida = list[PedidoSaida]


def para_entidades(dados: list[dict]) -> list[Pedido]:
    """Converte a lista JSON de `GET /pedidos` em entidades `Pedido`.

    Args:
        dados: Lista de dicionários, um por pedido, como devolvida pela API.

    Returns:
        Lista de `Pedido` (com seus itens) na mesma ordem de `dados`.

    Raises:
        pydantic.ValidationError: Se algum dicionário não corresponder ao formato esperado.
    """
    return [PedidoSaida.model_validate(d).para_entidade() for d in dados]