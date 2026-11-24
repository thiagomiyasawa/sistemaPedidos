"""Gráfico: evolução de pedidos criados ao longo do tempo (linha)."""

from __future__ import annotations

from collections import Counter

from PySide6.QtCharts import QCategoryAxis, QLineSeries, QScatterSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from client.paginas.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CORES,
    CartaoGrafico,
)


class EvolucaoPedidos(CartaoGrafico):
    """Cartão de gráfico de linha com a quantidade de pedidos criados por dia ou por mês.

    Attributes:
        titulo: Título exibido no cartão.
    """

    titulo = "Evolução de pedidos criados"

    def construir_filtros(self) -> None:
        """Cria a opção "Agrupar por" (Dia ou Mês) e redesenha o gráfico.

        Args:
            Nenhum.

        Returns:
            None. Adiciona um combo à barra de opções do cartão.
        """
        self.add_combo("agrupar", "Agrupar por", ["Dia", "Mês"])
        self.atualizar()

    def construir_grafico(self) -> None:
        """Conta os pedidos por data de criação (dia ou mês) e desenha linha com marcadores.

        Pedidos sem `data_criacao` são ignorados. Sem dados, apenas exibe a mensagem de vazio.

        Args:
            Nenhum. Usa os pedidos recebidos da página e a opção "agrupar".

        Returns:
            None. Adiciona séries (linha e pontos) e eixos ao gráfico do cartão.
        """
        fmt = "%Y-%m-%d" if self.valor("agrupar") == "Dia" else "%Y-%m"
        contagem = Counter(
            p.data_criacao.strftime(fmt) for p in self.pedidos() if p.data_criacao
        )
        linhas = sorted(contagem.items())
        self.mostrar(bool(linhas))
        if not linhas:
            return
        rotulos = [d for d, _ in linhas]
        serie = QLineSeries()
        serie.setName("Pedidos")
        serie.setColor(QColor(CORES[4]))
        serie.setPointLabelsVisible(True)
        serie.setPointLabelsFormat("@yPoint")
        for i, (_, n) in enumerate(linhas):
            serie.append(i, n)
        self.chart.addSeries(serie)
        # Eixo X numérico com rótulos sobre cada valor: funciona mesmo com um único ponto
        # (num QBarCategoryAxis o ponto único cairia na borda e a linha não apareceria).
        cat = QCategoryAxis()
        cat.setLabelsPosition(
            QCategoryAxis.AxisLabelsPosition.AxisLabelsPositionOnValue
        )
        for i, rotulo in enumerate(rotulos):
            cat.append(rotulo, i)
        cat.setRange(-0.5, len(rotulos) - 0.5)
        eixo_y = QValueAxis()
        eixo_y.setLabelFormat("%d")
        eixo_y.setRange(0, max(n for _, n in linhas) * 1.2)
        eixo_y.applyNiceNumbers()
        self.chart.addAxis(cat, Qt.AlignBottom)
        self.chart.addAxis(eixo_y, Qt.AlignLeft)
        serie.attachAxis(cat)
        serie.attachAxis(eixo_y)
        # Marcadores bem visíveis (o ponto do QLineSeries é minúsculo; com um único ponto some).
        marcas = QScatterSeries()
        marcas.setColor(QColor(CORES[4]))
        marcas.setBorderColor(QColor(CORES[4]))
        marcas.setMarkerSize(11)
        for i, (_, n) in enumerate(linhas):
            marcas.append(i, n)
        self.chart.addSeries(marcas)
        marcas.attachAxis(cat)
        marcas.attachAxis(eixo_y)
        self.chart.legend().setVisible(False)
