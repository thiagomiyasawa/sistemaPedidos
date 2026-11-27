"""Facade de métricas: consultas agregadas sobre pedidos e itens.

Depende apenas de `dbAdapterInterface`. Só lê; escrita e CRUD ficam em `FacedePedido`.

Uso:
    with DIC.db() as db:
        top = FacedeMetricas(db).top_itens(obra="A", limite=5)
"""
from __future__ import annotations

from datetime import datetime

from ..dbAdapterInterface import dbAdapterInterface
from .interfaces.facedeMetricasInterface import facedeMetricasInterface

_FORMATO_DATA = "%Y-%m-%d %H:%M:%S"  # como `data_criacao` é gravada (UTC, texto)
_COLUNAS_DISTINTAS = frozenset({"obra", "tarefa", "status_atual", "origem"})


class FacedeMetricas(facedeMetricasInterface):
    """Implementação SQL das consultas agregadas sobre pedidos e itens (somente leitura).

    Attributes:
        db: adapter de banco usado para executar as consultas.
    """

    def __init__(self, db: dbAdapterInterface) -> None:
        """Inicializa o facade com o adapter de banco.

        Args:
            db: adapter que satisfaz `dbAdapterInterface`.
        """
        self.db = db

    @staticmethod
    def _filtro_pedidos(obra: str | None, tarefa: str | None, status_atual: str | None,
                        origem: str | None, desde: datetime | None, ate: datetime | None) -> tuple[str, list]:
        """WHERE comum (sobre a tabela `pedido`, apelido `p`) e seus parâmetros.

        Args:
            obra: filtra por obra, se informada.
            tarefa: filtra por tarefa (exige `obra`).
            status_atual: filtra por status, se informado.
            origem: filtra por origem, se informada.
            desde: limite inferior inclusivo de `data_criacao`.
            ate: limite superior exclusivo de `data_criacao`.

        Returns:
            tuple[str, list]: cláusula WHERE (vazia se sem filtros) e lista de parâmetros.

        Raises:
            ValueError: se `tarefa` for informada sem `obra`.
        """
        if tarefa and not obra:
            raise ValueError("filtrar por tarefa exige informar a obra")
        filtros, params = [], []
        for col, val in (("p.obra", obra), ("p.tarefa", tarefa), ("p.status_atual", status_atual),
                         ("p.origem", origem)):
            if val:
                filtros.append(f"{col} = ?")
                params.append(val)
        # Texto 'YYYY-MM-DD HH:MM:SS': a comparação léxica equivale à cronológica.
        if desde:
            filtros.append("p.data_criacao >= ?")
            params.append(desde.strftime(_FORMATO_DATA))
        if ate:
            filtros.append("p.data_criacao < ?")
            params.append(ate.strftime(_FORMATO_DATA))
        return (f"WHERE {' AND '.join(filtros)}" if filtros else ""), params

    def _distintos(self, coluna: str, onde: str = "", params: tuple = ()) -> list[str]:
        """Valores distintos de uma coluna da tabela `pedido`, em ordem alfabética.

        Args:
            coluna: nome da coluna (constante interna, nunca vinda do usuário).
            onde: cláusula WHERE opcional, com marcadores `?`.
            params: parâmetros da cláusula `onde`.

        Returns:
            list[str]: valores distintos ordenados.

        Raises:
            ValueError: se `coluna` não for uma das colunas permitidas.
        """
        # `coluna` é interpolada no SQL: só aceita as colunas conhecidas.
        if coluna not in _COLUNAS_DISTINTAS:
            raise ValueError(f"coluna não permitida: {coluna}")
        self.db.execute(
            f"SELECT DISTINCT {coluna} AS v FROM pedido {onde} ORDER BY {coluna}", params)
        rows = self.db.fetch_all()
        return [r["v"] for r in rows]

    def valores_filtros(self) -> dict[str, list[str]]:
        """Valores distintos usados nos pedidos, para montar filtros.

        Returns:
            dict[str, list[str]]: chaves `obras`, `status` e `origens`, cada uma
            com a lista ordenada de valores distintos.
        """
        return {
            "obras": self._distintos("obra"),
            "status": self._distintos("status_atual"),
            "origens": self._distintos("origem"),
        }

    def tarefas_da_obra(self, obra: str) -> list[str]:
        """Tarefas distintas dos pedidos de uma obra.

        Args:
            obra: nome da obra (obrigatório).

        Returns:
            list[str]: tarefas em ordem alfabética.

        Raises:
            ValueError: se `obra` for vazia.
        """
        if not obra:
            raise ValueError("informe a obra para listar as tarefas")
        return self._distintos("tarefa", "WHERE obra = ?", (obra,))

    def top_itens(self, obra: str | None = None, tarefa: str | None = None,
                  status_atual: str | None = None, origem: str | None = None,
                  desde: datetime | None = None, ate: datetime | None = None,
                  limite: int = 10) -> list[tuple[str, int]]:
        """Top produtos por soma de quantidade nos itens dos pedidos filtrados.

        Args:
            obra: filtra por obra.
            tarefa: filtra por tarefa (exige `obra`).
            status_atual: filtra por status.
            origem: filtra por origem.
            desde: início do período (inclusivo) sobre `data_criacao`.
            ate: fim do período (exclusivo) sobre `data_criacao`.
            limite: quantidade máxima de produtos retornados.

        Returns:
            list[tuple[str, int]]: pares (produto, total), do maior para o menor
            (empates por ordem alfabética do produto).

        Raises:
            ValueError: se `tarefa` for informada sem `obra`.
        """
        where, params = self._filtro_pedidos(obra, tarefa, status_atual, origem, desde, ate)
        self.db.execute(
            "SELECT i.produto AS produto, SUM(i.quant) AS quantidade "
            "FROM item_pedido i JOIN pedido p ON p.id = i.id_pedido "
            f"{where} GROUP BY i.produto ORDER BY quantidade DESC, i.produto LIMIT ?",
            [*params, limite])
        rows = self.db.fetch_all()
        return [(r["produto"], r["quantidade"]) for r in rows]
