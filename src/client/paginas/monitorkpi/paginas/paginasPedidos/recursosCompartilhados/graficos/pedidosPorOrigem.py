"""Gráfico: pedidos por origem (pizza)."""

from __future__ import annotations

from collections import Counter

from PySide6.QtCharts import QPieSeries
from PySide6.QtGui import QColor

from client.paginas.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CORES,
    CartaoGrafico,
)


class PedidosPorOrigem(CartaoGrafico):
    """Cartão de gráfico de pizza (rosca) com a quantidade de pedidos por origem.

    Attributes:
        titulo: Título exibido no cartão.
    """

    titulo = "Pedidos por origem"

    def construir_filtros(self) -> None:
        """Não há opções próprias neste gráfico.

        Args:
            Nenhum.

        Returns:
            None.
        """
        pass

    def construir_grafico(self) -> None:
        """Conta os pedidos por origem e desenha uma rosca com fatias coloridas e rotuladas.

        Args:
            Nenhum. Usa os pedidos recebidos da página.

        Returns:
            None. Adiciona a série de pizza ao gráfico, ou exibe a mensagem de vazio se não há pedidos.
        """
        linhas = Counter(p.origem for p in self.pedidos()).most_common()
        self.mostrar(bool(linhas))
        if not linhas:
            return
        serie = QPieSeries()
        serie.setHoleSize(0.4)
        for i, (origem, n) in enumerate(linhas):
            fatia = serie.append(f"{origem} ({n})", n)
            fatia.setColor(QColor(CORES[i % len(CORES)]))
            fatia.setLabelVisible(True)
            fatia.setLabel(f"{origem}: {n}")
        self.chart.addSeries(serie)
        self.chart.legend().setVisible(True)
