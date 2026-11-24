"""Gráfico: pedidos por status (barras)."""

from __future__ import annotations

from collections import Counter

from client.paginas.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CORES,
    CartaoGrafico,
)
from client.paginas.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.dadosPedidos import (
    chave_status,
)


class PedidosPorStatus(CartaoGrafico):
    """Cartão de gráfico de barras com a quantidade de pedidos por status, na ordem do processo.

    Attributes:
        titulo: Título exibido no cartão.
    """

    titulo = "Pedidos por status"

    def construir_filtros(self) -> None:
        """Não há opções próprias neste gráfico.

        Args:
            Nenhum.

        Returns:
            None.
        """
        pass

    def construir_grafico(self) -> None:
        """Conta os pedidos por `status_atual` e desenha as barras ordenadas por `chave_status`.

        Args:
            Nenhum. Usa os pedidos recebidos da página.

        Returns:
            None. Desenha as barras, ou exibe a mensagem de vazio se não há pedidos.
        """
        contagem = Counter(p.status_atual for p in self.pedidos())
        linhas = sorted(
            contagem.items(), key=lambda x: chave_status(x[0])
        )  # ordem do processo
        self.mostrar(bool(linhas))
        if linhas:
            self.barras([s for s, _ in linhas], [n for _, n in linhas], cor=CORES[0])
