"""GET /health — sem entrada."""
from __future__ import annotations

from pydantic import BaseModel


class HealthSaida(BaseModel):
    """Resposta do health check da API.

    Campos:
        status: Situação geral do serviço (ex.: "ok").
        tabelas: Mapa nome da tabela -> True se ela está acessível/existente.
    """

    status: str
    tabelas: dict[str, bool]