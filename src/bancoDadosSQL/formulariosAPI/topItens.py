"""GET /itens/top — itens mais solicitados (soma de `quant` por produto), filtrados, só o top N."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .validacoes import INT_MAX, Obra, Origem, Status, Tarefa


class TopItensEntrada(BaseModel):
    """Filtros (query string). O período é `dias` (últimos N dias) OU `de`/`ate` (datas inclusivas)."""

    model_config = ConfigDict(extra="forbid")  # parâmetros desconhecidos → 422

    obra: Obra | None = None
    tarefa: Tarefa | None = None
    status_atual: Status | None = None
    origem: Origem | None = None
    dias: int | None = Field(None, ge=1, le=36500, description="Últimos N dias (a partir de agora, UTC)")
    de: date | None = Field(None, description="Pedidos criados a partir desta data (inclusive)")
    ate: date | None = Field(None, description="Pedidos criados até esta data (inclusive)")
    limite: int = Field(10, ge=1, le=100, description="Quantidade de itens no top")

    @model_validator(mode="after")
    def _periodo_coerente(self) -> TopItensEntrada:
        """Valida a coerência entre os filtros informados.

        Returns:
            A própria instância, se válida.

        Raises:
            ValueError: Se `tarefa` for enviada sem `obra`, se `dias` for combinado com
                `de`/`ate`, ou se `de` for posterior a `ate`.
        """
        if self.tarefa and not self.obra:
            raise ValueError("`tarefa` exige `obra`: a tarefa só tem sentido dentro de uma obra")
        if self.dias is not None and (self.de or self.ate):
            raise ValueError("use `dias` ou `de`/`ate`, não os dois")
        if self.de and self.ate and self.de > self.ate:
            raise ValueError("`de` não pode ser depois de `ate`")
        return self

    def periodo(self) -> tuple[datetime | None, datetime | None]:
        """Intervalo [desde, ate_exclusivo) em UTC, como `data_criacao` é gravada (sem fuso).

        Returns:
            Tupla (desde, ate_exclusivo); cada limite é `None` quando não definido.
            Com `dias`, `desde` é agora menos N dias e o fim é `None`; com `de`/`ate`,
            o fim é o início do dia seguinte a `ate`.
        """
        if self.dias is not None:
            agora = datetime.now(timezone.utc).replace(tzinfo=None)
            return agora - timedelta(days=self.dias), None
        desde = datetime.combine(self.de, datetime.min.time()) if self.de else None
        ate = datetime.combine(self.ate + timedelta(days=1), datetime.min.time()) if self.ate else None
        return desde, ate


class ItemTopSaida(BaseModel):
    """Um item do ranking dos mais solicitados.

    Campos:
        produto: Nome do produto.
        quantidade: Soma das quantidades solicitadas desse produto.
    """

    model_config = ConfigDict(from_attributes=True)

    produto: str
    quantidade: int = Field(ge=0, le=INT_MAX * 500)  # soma de várias quantidades


TopItensSaida = list[ItemTopSaida]
