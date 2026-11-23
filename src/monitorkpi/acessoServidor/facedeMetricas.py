"""Facade de métricas sobre a API HTTP.

`FacedeMetricasAPI` consulta os endpoints de métricas (consultas agregadas calculadas no
servidor). Fala com o servidor pelo `adapterAPIInterface` (injetado; por padrão `AdapterAPI`).
A validação dos filtros e a conversão do JSON ficam em `formulariosAPI.topItens`.

Uso:
    with FacedeMetricasAPI() as metricas:
        top = metricas.top_itens(obra="Subestação Alfa", dias=7, limite=5)
        # [("Parafuso M12", 131), ("Quadro de comando", 33), ...]
"""
from __future__ import annotations

from datetime import date
from typing import Self

from monitorkpi.acessoServidor.adapterAPI import AdapterAPI
from monitorkpi.acessoServidor.formulariosAPI import topItens, valoresFiltros
from monitorkpi.acessoServidor.formulariosAPI.topItens import TopItensEntrada
from monitorkpi.acessoServidor.formulariosAPI.valoresFiltros import TarefasEntrada
from monitorkpi.acessoServidor.interfaces.adapterAPIInterface import adapterAPIInterface
from monitorkpi.acessoServidor.interfaces.facedeMetricasAPIInterface import facedeMetricasAPIInterface


class FacedeMetricasAPI(facedeMetricasAPIInterface):
    """Facade de métricas que consulta os endpoints agregados da API HTTP.

    Atributos:
        api: adapter de transporte usado nas requisições.
    """

    def __init__(self, api: adapterAPIInterface | None = None) -> None:
        """Inicializa o facade.

        Args:
            api: adapter HTTP a usar; se None cria um `AdapterAPI` padrão.
        """
        self.api: adapterAPIInterface = api or AdapterAPI()

    # --- ciclo de vida: fecha o adapter ------------------------------------
    def close(self) -> None:
        """Fecha o adapter e libera a conexão.

        Returns:
            None.
        """
        self.api.close()

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
        """Obtém os valores distintos usados nos filtros da interface.

        Returns:
            Dicionário com as listas `obras`, `status` e `origens`, em ordem alfabética.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        return valoresFiltros.para_dict(self.api.get("/filtros"))

    def tarefas_da_obra(self, obra: str) -> list[str]:
        """Lista as tarefas distintas de uma obra.

        Args:
            obra: nome da obra (obrigatório).

        Returns:
            Tarefas da obra em ordem alfabética.

        Raises:
            ValueError: se a obra for inválida/vazia (validação do formulário,
                antes de chamar a API).
            ApiError: em falha de comunicação com a API.
        """
        filtro = TarefasEntrada(obra=obra)  # valida antes de chamar: sem obra, nem requisita
        return valoresFiltros.para_lista(self.api.get("/filtros/tarefas", **filtro.params()))

    def top_itens(self, obra: str | None = None, tarefa: str | None = None,
                  status_atual: str | None = None, origem: str | None = None,
                  dias: int | None = None,
                  de: date | None = None, ate: date | None = None,
                  limite: int = 10) -> list[tuple[str, int]]:
        """Obtém os produtos mais pedidos (soma de quantidade).

        Args:
            obra: filtra por obra, ou None.
            tarefa: filtra por tarefa, ou None.
            status_atual: filtra por status do pedido, ou None.
            origem: filtra por origem do pedido, ou None.
            dias: considera os últimos N dias; exclusivo com `de`/`ate`.
            de: data inicial inclusiva do período, ou None.
            ate: data final inclusiva do período, ou None.
            limite: número máximo de produtos retornados.

        Returns:
            Lista de tuplas (produto, total), do maior para o menor.

        Raises:
            ValueError: se os filtros forem inválidos (validação do formulário).
            ApiError: em falha de comunicação com a API.
        """
        filtro = TopItensEntrada(obra=obra, tarefa=tarefa, status_atual=status_atual,
                                 origem=origem, dias=dias, de=de, ate=ate, limite=limite)
        return topItens.para_tuplas(self.api.get("/itens/top", **filtro.params()))
