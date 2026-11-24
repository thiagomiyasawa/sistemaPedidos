"""Gráfico: produtos mais solicitados por quantidade (barras horizontais)."""

from __future__ import annotations

from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CORES,
    CartaoGrafico,
)
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.dadosPedidos import (
    LIMITE_TOP_ITENS,
)


class TopProdutos(CartaoGrafico):
    """Cartão de gráfico de barras horizontais com os produtos mais solicitados (quantidade total).

    Attributes:
        titulo: Título exibido no cartão.
        precisa_top_itens: True; indica à página que deve buscar o top de itens.
    """

    titulo = "Produtos mais solicitados (quantidade)"
    precisa_top_itens = (
        True  # a página consulta o facade de métricas e entrega o top pronto
    )

    def construir_filtros(self) -> None:
        """Cria o campo numérico "Top" (de 3 até `LIMITE_TOP_ITENS`, padrão 5).

        Args:
            Nenhum.

        Returns:
            None. Adiciona um spin à barra de opções do cartão.
        """
        self.add_spin("topn", "Top", 3, LIMITE_TOP_ITENS, 5)

    def construir_grafico(self) -> None:
        """Desenha os N primeiros itens do top (N = opção "topn"), maior no topo.

        Args:
            Nenhum. Usa o top de itens recebido da página.

        Returns:
            None. Desenha as barras horizontais, ou exibe a mensagem de vazio se não há itens.
        """
        linhas = self.top_itens()[: self.valor("topn")]  # já vem do maior para o menor
        self.mostrar(bool(linhas))
        if linhas:
            linhas = linhas[::-1]  # maior no topo no gráfico horizontal
            self.barras(
                [pr for pr, _ in linhas],
                [q for _, q in linhas],
                horizontal=True,
                cor=CORES[1],
            )
