"""Interface (contrato) do facade de métricas usado pelo cliente.

Satisfazem este contrato `FacedeMetricasAPI` (via HTTP) e `FacedeMetricasTeste` (direto no
banco), podendo ser trocados no `DIC` sem alterar quem os usa. O período segue o da API
(`dias` ou `de`/`ate`), e não os `datetime` do facade SQL.
"""
from __future__ import annotations

from datetime import date
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class facedeMetricasAPIInterface(Protocol):
    """Consultas agregadas de pedidos/itens, mais o ciclo de vida."""

    def valores_filtros(self) -> dict[str, list[str]]:
        """Valores distintos dos pedidos, em ordem alfabética: `obras`, `status` e `origens`.

        Returns:
            Dicionário com as listas `obras`, `status` e `origens`.
        """
        ...

    def tarefas_da_obra(self, obra: str) -> list[str]:
        """Tarefas distintas da obra, em ordem alfabética. A obra é obrigatória.

        Args:
            obra: nome da obra (obrigatório).

        Returns:
            Lista de tarefas da obra.

        Raises:
            ValueError: se a obra for vazia/inválida.
        """
        ...

    def top_itens(
        self,
        obra: str | None = None,
        tarefa: str | None = None,
        status_atual: str | None = None,
        origem: str | None = None,
        dias: int | None = None,
        de: date | None = None,
        ate: date | None = None,
        limite: int = 10,
    ) -> list[tuple[str, int]]:
        """Top `limite` produtos por soma de quantidade, como (produto, total), do maior ao menor.

        Período: `dias` (últimos N dias) ou `de`/`ate` (datas inclusivas); sem nenhum, todo o histórico.

        Args:
            obra: filtra por obra, ou None.
            tarefa: filtra por tarefa, ou None.
            status_atual: filtra por status do pedido, ou None.
            origem: filtra por origem do pedido, ou None.
            dias: últimos N dias; alternativo a `de`/`ate`.
            de: data inicial inclusiva, ou None.
            ate: data final inclusiva, ou None.
            limite: número máximo de produtos retornados.

        Returns:
            Lista de tuplas (produto, total), do maior para o menor.

        Raises:
            ValueError: se os filtros forem inválidos.
        """
        ...

    def close(self) -> None:
        """Libera a conexão/recursos.

        Returns:
            None.
        """
        ...

    def __enter__(self) -> Self:
        """Entra no contexto `with`.

        Returns:
            O próprio facade.
        """
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o facade.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None.
        """
        ...
