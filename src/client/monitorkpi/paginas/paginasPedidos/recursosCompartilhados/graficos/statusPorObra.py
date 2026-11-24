"""Gráfico: status por obra (barras empilhadas)."""

from __future__ import annotations

from collections import Counter

from PySide6.QtCharts import QBarCategoryAxis, QBarSet, QStackedBarSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CORES,
    CartaoGrafico,
)
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.dadosPedidos import (
    chave_status,
)


class StatusPorObra(CartaoGrafico):
    """Cartão de gráfico de barras empilhadas: uma barra por obra, empilhada por status.

    Attributes:
        titulo: Título exibido no cartão.
    """

    titulo = "Status por obra (empilhado)"

    def construir_filtros(self) -> None:
        """Não há opções próprias neste gráfico.

        Args:
            Nenhum.

        Returns:
            None.
        """
        pass

    def construir_grafico(self) -> None:
        """Conta pedidos por (obra, status) e desenha as barras empilhadas com legenda.

        Os status seguem a ordem do processo (`chave_status`) e as obras a ordem alfabética.

        Args:
            Nenhum. Usa os pedidos recebidos da página.

        Returns:
            None. Adiciona série e eixos ao gráfico, ou exibe a mensagem de vazio se não há pedidos.
        """
        mapa = Counter((p.obra, p.status_atual) for p in self.pedidos())
        linhas = list(mapa)
        self.mostrar(bool(linhas))
        if not linhas:
            return
        obras = sorted({o for o, _ in linhas})
        status = sorted({s for _, s in linhas}, key=chave_status)  # ordem do processo
        serie = QStackedBarSeries()
        for i, s in enumerate(status):
            conj = QBarSet(s)
            conj.setColor(QColor(CORES[i % len(CORES)]))
            conj.append([mapa.get((o, s), 0) for o in obras])
            serie.append(conj)
        self.chart.addSeries(serie)
        cat = QBarCategoryAxis()
        cat.append(obras)
        val = QValueAxis()
        val.setLabelFormat("%d")
        totais = [sum(mapa.get((o, s), 0) for s in status) for o in obras]
        val.setRange(0, max(totais) * 1.1)
        val.applyNiceNumbers()
        self.chart.addAxis(cat, Qt.AlignBottom)
        self.chart.addAxis(val, Qt.AlignLeft)
        serie.attachAxis(cat)
        serie.attachAxis(val)
        self.chart.legend().setVisible(True)
