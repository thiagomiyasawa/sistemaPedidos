"""Facade de métricas para testes: liga direto ao banco SQLite, sem passar pela API.

Reaproveita o `FacedeMetricas` do módulo `bancoDadosSQL` e adapta a assinatura ao contrato do
cliente (`facedeMetricasAPIInterface`), de modo que pode ser usado no lugar do `FacedeMetricasAPI`.
"""

from __future__ import annotations

from datetime import date
from typing import Self

from bancoDadosSQL.dbAdapterInterface import dbAdapterInterface
from bancoDadosSQL.facedes.facedeMetricas import FacedeMetricas
from bancoDadosSQL.SQLite.SQLiteAdapter import SQLiteAdapter
from client.monitorkpi.acessoServidor.formulariosAPI.topItens import TopItensEntrada
from client.monitorkpi.acessoServidor.formulariosAPI.valoresFiltros import (
    TarefasEntrada,
)
from client.monitorkpi.acessoServidor.interfaces.facedeMetricasAPIInterface import (
    facedeMetricasAPIInterface,
)


class FacedeMetricasTeste(facedeMetricasAPIInterface):
    """Facade de métricas para testes, ligado direto ao banco (sem API).

    Atributos:
        db: adapter de banco de dados em uso.
        _metricas: `FacedeMetricas` do `bancoDadosSQL` que executa as consultas.
    """

    def __init__(self, db: dbAdapterInterface | None = None) -> None:
        """Inicializa o facade.

        Args:
            db: adapter de banco; se None cria um `SQLiteAdapter` padrão.
        """
        self.db = db or SQLiteAdapter()
        self._metricas = FacedeMetricas(self.db)

    # --- ciclo de vida -----------------------------------------------------
    def close(self) -> None:
        """Fecha a conexão com o banco.

        Returns:
            None.
        """
        self.db.close()

    def __enter__(self) -> Self:
        """Entra no contexto `with`.

        Returns:
            O próprio facade.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o facade.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None (exceções não são suprimidas).
        """
        self.close()

    # --- métricas ----------------------------------------------------------
    def valores_filtros(self) -> dict[str, list[str]]:
        """Obtém os valores distintos usados nos filtros.

        Returns:
            Dicionário com as listas `obras`, `status` e `origens`, em ordem alfabética.
        """
        return self._metricas.valores_filtros()

    def tarefas_da_obra(self, obra: str) -> list[str]:
        """Lista as tarefas distintas de uma obra.

        Args:
            obra: nome da obra (obrigatório).

        Returns:
            Tarefas da obra em ordem alfabética.

        Raises:
            ValueError: se a obra for inválida/vazia (mesma validação do endpoint).
        """
        filtro = TarefasEntrada(obra=obra)  # mesma validação do endpoint
        return self._metricas.tarefas_da_obra(filtro.obra)

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
        """Obtém os produtos mais pedidos (soma de quantidade).

        Args:
            obra: filtra por obra, ou None.
            tarefa: filtra por tarefa, ou None.
            status_atual: filtra por status do pedido, ou None.
            origem: filtra por origem do pedido, ou None.
            dias: considera os últimos N dias; alternativo a `de`/`ate`.
            de: data inicial inclusiva, ou None.
            ate: data final inclusiva, ou None.
            limite: número máximo de produtos retornados.

        Returns:
            Lista de tuplas (produto, total), do maior para o menor.

        Raises:
            ValueError: se os filtros forem inválidos (mesma validação do endpoint).
        """
        # Mesma validação e mesma regra de período do endpoint.
        filtro = TopItensEntrada(
            obra=obra,
            tarefa=tarefa,
            status_atual=status_atual,
            origem=origem,
            dias=dias,
            de=de,
            ate=ate,
            limite=limite,
        )
        desde, fim = filtro.periodo()
        return self._metricas.top_itens(
            filtro.obra,
            filtro.tarefa,
            filtro.status_atual,
            filtro.origem,
            desde,
            fim,
            filtro.limite,
        )
