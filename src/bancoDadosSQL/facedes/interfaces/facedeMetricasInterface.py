"""Interface (contrato) do facade de métricas.

Consultas agregadas (somas, rankings, contagens) sobre pedidos e itens, calculadas no banco.
Fica separado de `facedePedidoInterface`, que cuida do CRUD das entidades.
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class facedeMetricasInterface(Protocol):
    """Operações de leitura agregada sobre pedidos e itens."""

    def valores_filtros(self) -> dict[str, list[str]]:
        """Valores distintos usados nos pedidos, em ordem alfabética: `obras`, `status` e `origens`.

        Returns:
            dict[str, list[str]]: chaves `obras`, `status` e `origens` com listas ordenadas.
        """
        ...

    def tarefas_da_obra(self, obra: str) -> list[str]:
        """Tarefas distintas dos pedidos da obra, em ordem alfabética.

        A obra é obrigatória (tarefa só existe dentro de uma obra): vazia → `ValueError`.

        Args:
            obra: nome da obra.

        Returns:
            list[str]: tarefas distintas em ordem alfabética.

        Raises:
            ValueError: se `obra` for vazia.
        """
        ...

    def top_itens(
        self,
        obra: str | None = None,
        tarefa: str | None = None,
        status_atual: str | None = None,
        origem: str | None = None,
        desde: datetime | None = None,
        ate: datetime | None = None,
        limite: int = 10,
    ) -> list[tuple[str, int]]:
        """Top `limite` produtos por soma de quantidade, como (produto, total), do maior ao menor.

        Filtra os pedidos por obra, tarefa, status, origem e `desde <= data_criacao < ate` (UTC, sem fuso).

        Args:
            obra: filtra por obra.
            tarefa: filtra por tarefa (exige `obra`).
            status_atual: filtra por status.
            origem: filtra por origem.
            desde: início do período (inclusivo).
            ate: fim do período (exclusivo).
            limite: máximo de produtos retornados.

        Returns:
            list[tuple[str, int]]: pares (produto, total), do maior ao menor.

        Raises:
            ValueError: se `tarefa` for informada sem `obra`.
        """
        ...
