"""Página de KPIs de pedidos - por obra (PySide6).

Escolhe-se uma obra e os gráficos mostram só os pedidos dela; tarefa, status, origem e período
(pronto ou personalizado) filtram em conjunto.
Reaproveita os cartões de `paginaPedidosGeral.graficos` que fazem sentido para uma única obra.
Execução:
    .venv\\Scripts\\python.exe "src/monitorkpi/paginas/paginasPedidos/paginaPedidosObra/paginaObra.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite rodar o arquivo diretamente: coloca `src` no path (antes dos imports do projeto).
_SRC = Path(__file__).resolve().parents[4]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from PySide6.QtCore import QDate  # noqa: E402
from PySide6.QtWidgets import QDateEdit  # noqa: E402

from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CartaoGrafico,
)  # noqa: E402
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.dadosPedidos import (  # noqa: E402
    PERIODO_PADRAO,
    PERIODOS,
    TODOS,
    tarefas_da_obra,
    valores_distintos,
)
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.paginaBase import (
    PaginaKPIBase,
    executar,
)  # noqa: E402
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.graficos import (  # noqa: E402
    EvolucaoPedidos,
    PedidosPorStatus,
    TopProdutos,
)

PERSONALIZADO = "Personalizado"


class PaginaKPIPedidosObra(PaginaKPIBase):
    """Grade de cartões de gráficos de uma obra selecionada.

    Attributes:
        TITULO: Título do cabeçalho da página.
        COLUNAS: Número de colunas da grade (1).
        data_de: Campo de data inicial do período personalizado.
        data_ate: Campo de data final do período personalizado.
        caixa_de: Contêiner do campo "De" (visível só no período personalizado).
        caixa_ate: Contêiner do campo "Até" (visível só no período personalizado).
    """

    TITULO = "KPIs de Pedidos por Obra"
    COLUNAS = 1  # um gráfico embaixo do outro

    def criar_cartoes(self) -> list[CartaoGrafico]:
        """Cria os cartões da página por obra.

        Args:
            Nenhum.

        Returns:
            Lista com `PedidosPorStatus`, `EvolucaoPedidos` e `TopProdutos`.
        """
        return [PedidosPorStatus(), EvolucaoPedidos(), TopProdutos()]

    def construir_filtros(self) -> None:
        """Monta os filtros: obra, tarefa, status, origem, período e datas "De"/"Até".

        As datas só aparecem quando o período é "Personalizado". A lista de tarefas
        depende da obra selecionada.

        Args:
            Nenhum.

        Returns:
            None.
        """
        obras = valores_distintos("obra")
        self.add_combo("obra", "Obra", obras, ao_mudar=self.obra_mudou)
        tarefas = tarefas_da_obra(obras[0]) if obras else []  # a tarefa depende da obra
        self.add_combo("tarefa", "Tarefa", [TODOS, *tarefas])
        self.add_combo("status", "Status", [TODOS, *valores_distintos("status_atual")])
        self.add_combo("origem", "Origem", [TODOS, *valores_distintos("origem")])
        self.add_combo(
            "periodo", "Período", [*PERIODOS, PERSONALIZADO], padrao=PERIODO_PADRAO
        )
        self.filtros["periodo"].currentIndexChanged.connect(self._atualizar_datas)

        hoje = QDate.currentDate()
        self.data_de = QDateEdit(hoje.addDays(-7))
        self.data_ate = QDateEdit(hoje)
        for d in (self.data_de, self.data_ate):
            d.setCalendarPopup(True)
            d.setDisplayFormat("dd/MM/yyyy")
            d.dateChanged.connect(self.aplicar_filtros)
        self.caixa_de = self.add_controle("De", self.data_de)
        self.caixa_ate = self.add_controle("Até", self.data_ate)
        self._atualizar_datas()

    def _atualizar_datas(self) -> None:
        """Mostra os campos de data só quando o período é "Personalizado".

        Args:
            Nenhum.

        Returns:
            None.
        """
        personalizado = self.filtros["periodo"].currentText() == PERSONALIZADO
        self.caixa_de.setVisible(personalizado)
        self.caixa_ate.setVisible(personalizado)

    def obra_mudou(self) -> None:
        """Recarrega as tarefas da nova obra (volta para "Todos") e redesenha.

        Args:
            Nenhum. Usa a obra selecionada no combo "obra".

        Returns:
            None.
        """
        cb = self.filtros["tarefa"]
        cb.blockSignals(True)
        cb.clear()
        cb.addItems([TODOS, *tarefas_da_obra(self.filtros["obra"].currentText())])
        cb.blockSignals(False)
        self.aplicar_filtros()

    def filtros_atuais(self) -> dict:
        """Lê os filtros escolhidos na tela.

        Args:
            Nenhum.

        Returns:
            Dicionário com `obra`, `tarefa`, `status`, `origem` e o período: `de`/`ate`
            (`date`, já ordenadas) se "Personalizado", ou `dias` (int ou None) caso contrário.
        """
        f = {
            "obra": self.filtros["obra"].currentText(),
            "tarefa": self.filtros["tarefa"].currentText(),
            "status": self.filtros["status"].currentText(),
            "origem": self.filtros["origem"].currentText(),
        }
        periodo = self.filtros["periodo"].currentText()
        if periodo == PERSONALIZADO:
            de, ate = self.data_de.date().toPython(), self.data_ate.date().toPython()
            f["de"], f["ate"] = min(de, ate), max(de, ate)
        else:
            f["dias"] = PERIODOS[periodo]
        return f


def main() -> None:
    """Abre a página de KPIs por obra em uma janela própria.

    Args:
        Nenhum.

    Returns:
        None. Bloqueia até a janela ser fechada.
    """
    executar(PaginaKPIPedidosObra, "Monitor KPI - Pedidos por obra")


if __name__ == "__main__":
    main()
