"""Gráfico: pedidos por obra (barras horizontais)."""

from __future__ import annotations

from collections import Counter

from client.paginas.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CORES,
    CartaoGrafico,
)


class PedidosPorObra(CartaoGrafico):
    """Cartão de gráfico de barras horizontais com a quantidade de pedidos de cada obra.

    Attributes:
        titulo: Título exibido no cartão.
    """

    titulo = "Pedidos por obra"

    def construir_filtros(self) -> None:
        """Não há opções próprias neste gráfico.

        Args:
            Nenhum.

        Returns:
            None.
        """
        pass

    def construir_grafico(self) -> None:
        """Conta os pedidos por obra (ordem crescente) e desenha as barras horizontais.

        Args:
            Nenhum. Usa os pedidos recebidos da página.

        Returns:
            None. Desenha as barras no gráfico, ou exibe a mensagem de vazio se não há pedidos.
        """
        linhas = sorted(
            Counter(p.obra for p in self.pedidos()).items(), key=lambda x: x[1]
        )
        self.mostrar(bool(linhas))
        if linhas:
            self.barras(
                [o for o, _ in linhas],
                [n for _, n in linhas],
                horizontal=True,
                cor=CORES[2],
            )
