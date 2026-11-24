"""GET /itens/top — filtros (query string) e lista dos itens mais solicitados."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .validacoes import INT_MAX, Obra, Origem, Status, Tarefa


class TopItensEntrada(BaseModel):
    """Filtros do top. O período é `dias` (últimos N dias) OU `de`/`ate` (datas inclusivas)."""

    model_config = ConfigDict(extra="forbid")  # parâmetros desconhecidos → erro

    obra: Obra | None = None
    tarefa: Tarefa | None = None
    status_atual: Status | None = None
    origem: Origem | None = None
    dias: int | None = Field(None, ge=1, le=36500)
    de: date | None = None
    ate: date | None = None
    limite: int = Field(10, ge=1, le=100)

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

    def params(self) -> dict:
        """Parâmetros da query string (sem os não informados; datas em ISO).

        Returns:
            Dicionário com os filtros diferentes de `None`, serializável em JSON.
        """
        return self.model_dump(exclude_none=True, mode="json")

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

    produto: str
    quantidade: int = Field(ge=0, le=INT_MAX * 500)  # soma de várias quantidades


TopItensSaida = list[ItemTopSaida]


def para_tuplas(dados: list[dict]) -> list[tuple[str, int]]:
    """Converte a lista JSON de `GET /itens/top` em tuplas (produto, quantidade total).

    Args:
        dados: Lista de dicionários com `produto` e `quantidade`, como devolvida pela API.

    Returns:
        Lista de tuplas (produto, quantidade) na mesma ordem de `dados`.

    Raises:
        pydantic.ValidationError: Se algum dicionário não corresponder ao formato esperado.
    """
    return [(i.produto, i.quantidade) for i in (ItemTopSaida.model_validate(d) for d in dados)]
