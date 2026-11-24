"""Página de KPIs de pedidos - visão geral (PySide6).

Reúne os gráficos gerais da pasta `graficos`; todos obedecem a um filtro geral (status, origem, período).
Execução:
    .venv\\Scripts\\python.exe "src/monitorkpi/paginas/paginasPedidos/paginaPedidosGeral/paginaGeral.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite rodar o arquivo diretamente: coloca `src` no path (antes dos imports do projeto).
_SRC = Path(__file__).resolve().parents[4]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CartaoGrafico,
)  # noqa: E402
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.dadosPedidos import (  # noqa: E402
    PERIODO_PADRAO,
    PERIODOS,
    TODOS,
    valores_distintos,
)
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.paginaBase import (
    PaginaKPIBase,
    executar,
)  # noqa: E402
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.graficos import (  # noqa: E402
    EvolucaoPedidos,
    PedidosPorObra,
    PedidosPorStatus,
    StatusPorObra,
    TopProdutos,
)


class PaginaKPIPedidos(PaginaKPIBase):
    """Grade de cartões de gráficos da visão geral, com filtros de status, origem e período.

    Attributes:
        TITULO: Título do cabeçalho da página.
        COLUNAS: Número de colunas da grade (1).
    """

    TITULO = "KPIs de Pedidos"
    COLUNAS = 1  # um gráfico embaixo do outro

    def criar_cartoes(self) -> list[CartaoGrafico]:
        """Cria os cartões da visão geral.

        Args:
            Nenhum.

        Returns:
            Lista com `PedidosPorStatus`, `PedidosPorObra`, `EvolucaoPedidos`, `TopProdutos`
            e `StatusPorObra`, nessa ordem.
        """
        return [
            PedidosPorStatus(),
            PedidosPorObra(),
            EvolucaoPedidos(),
            TopProdutos(),
            StatusPorObra(),
        ]

    def construir_filtros(self) -> None:
        """Monta os combos de filtro: Status, Origem e Período.

        Args:
            Nenhum.

        Returns:
            None.
        """
        self.add_combo("status", "Status", [TODOS, *valores_distintos("status_atual")])
        self.add_combo("origem", "Origem", [TODOS, *valores_distintos("origem")])
        self.add_combo("periodo", "Período", list(PERIODOS), padrao=PERIODO_PADRAO)

    def filtros_atuais(self) -> dict:
        """Lê os filtros escolhidos na tela.

        Args:
            Nenhum.

        Returns:
            Dicionário com `status`, `origem` e `dias` (int de dias ou None para todo o período).
        """
        return {
            "status": self.filtros["status"].currentText(),
            "origem": self.filtros["origem"].currentText(),
            "dias": PERIODOS[self.filtros["periodo"].currentText()],
        }


def main() -> None:
    """Abre a página de KPIs gerais em uma janela própria.

    Args:
        Nenhum.

    Returns:
        None. Bloqueia até a janela ser fechada.
    """
    executar(PaginaKPIPedidos, "Monitor KPI - Pedidos")


if __name__ == "__main__":
    main()
