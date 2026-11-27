"""Página "Meus pedidos": os pedidos do usuário e, ao selecionar um, os itens dele (PySide6).

Os pedidos vêm da API pelo facade de pedidos (`DIC.facede_pedido()`), só os do usuário
autenticado, do mais novo para o mais antigo. A paginação dos pedidos é feita no servidor: a tela
pede só os 30 da página atual (e o filtro de status vai junto na consulta). Os itens do pedido
selecionado são buscados na primeira vez que ele é escolhido e paginados na tela. Falhas da API aparecem em vermelho no topo.

Execução (a chave deve estar em `MONITORKPI_API_KEY`):
    .venv/Scripts/python.exe "src/client/paginas/sisPedidos/paginaMeusPedidos/paginaMeusPedidos.py"
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# Permite rodar o arquivo diretamente: coloca `src` no path (antes dos imports do projeto).
_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractItemView,
    QApplication,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from bancoDadosSQL.entidades.pedidos import Pedido  # noqa: E402
from client.adapters.interfaces.adapterAPIInterface import ApiError  # noqa: E402
from client.componentes.barraPaginacao import BarraPaginacao  # noqa: E402
from client.DIC import DIC  # noqa: E402
from client.facedes.interfaces.facedePedidoAPIInterface import (  # noqa: E402
    facedePedidoAPIInterface,
)

TODOS = "Todos"

ESTILO = """
QWidget { font-size: 10pt; }
#cabecalho { font-size: 15pt; font-weight: 700; }
#subtitulo { font-size: 11pt; font-weight: 600; }
#rotuloFiltro { font-size: 8pt; color: palette(placeholder-text); }
#vazio { color: palette(placeholder-text); }
#erro { color: #c0392b; }
"""


def formatar_data_hora(valor: datetime | None) -> str:
    """Data/hora de criação (gravada em UTC, sem fuso) no horário local, dd/mm/aaaa hh:mm.

    Args:
        valor: instante em UTC (sem fuso) ou None.

    Returns:
        str: texto formatado, ou "—" se não houver data.
    """
    if valor is None:
        return "—"
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=UTC)
    return valor.astimezone().strftime("%d/%m/%Y %H:%M")


def _tabela(colunas: list[str], stretch: int) -> QTableWidget:
    """Tabela somente leitura, de seleção por linha, com o cabeçalho alinhado ao conteúdo.

    Args:
        colunas: títulos das colunas.
        stretch: índice da coluna que ocupa o espaço restante.

    Returns:
        QTableWidget: tabela vazia pronta para uso.
    """
    t = QTableWidget(0, len(colunas))
    t.setHorizontalHeaderLabels(colunas)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.verticalHeader().setVisible(False)
    cab = t.horizontalHeader()
    cab.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    for c in range(len(colunas)):
        cab.setSectionResizeMode(c, QHeaderView.Stretch if c == stretch else QHeaderView.ResizeToContents)
    return t


class PaginaMeusPedidos(QWidget):
    """Lista dos pedidos do usuário (em cima) e itens do pedido selecionado (embaixo).

    Attributes:
        visiveis: Pedidos da página atual, do mais novo para o mais antigo.
        status: Combo de filtro por status.
        tabela_pedidos: Tabela dos pedidos (30 por página, paginada no servidor).
        paginacao_pedidos: Barra de páginas dos pedidos (alimentada com o total da API).
        tabela_itens: Tabela dos itens do pedido selecionado (30 por página).
        paginacao_itens: Barra de paginação da tabela de itens.
        rotulo_erro: Mensagem da última falha ao acessar a API.
    """

    TITULO = "Meus pedidos"

    def __init__(self, facede: facedePedidoAPIInterface | None = None) -> None:
        """Monta a página e carrega os pedidos.

        Args:
            facede: facade de pedidos; se None usa `DIC.facede_pedido()`.
        """
        super().__init__()
        self.setStyleSheet(ESTILO)
        self._facede = facede
        self._itens_cache: dict[int, list] = {}
        self._itens_exibidos: list = []  # itens do pedido selecionado, de todas as páginas
        self.visiveis: list[Pedido] = []

        cab = QLabel(self.TITULO)
        cab.setObjectName("cabecalho")
        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)
        topo = QHBoxLayout()
        topo.addWidget(cab)
        topo.addStretch(1)
        topo.addWidget(atualizar)

        self.rotulo_erro = QLabel("")
        self.rotulo_erro.setObjectName("erro")
        self.rotulo_erro.setWordWrap(True)
        self.rotulo_erro.hide()

        self.status = QComboBox()
        self.status.addItem(TODOS)
        self.status.currentIndexChanged.connect(self._filtro_mudou)
        rotulo_status = QLabel("Status")
        rotulo_status.setObjectName("rotuloFiltro")
        filtro = QVBoxLayout()
        filtro.setSpacing(2)
        filtro.addWidget(rotulo_status)
        filtro.addWidget(self.status)
        barra = QHBoxLayout()
        barra.addLayout(filtro)
        barra.addStretch(1)

        self.tabela_pedidos = _tabela(
            ["Nº", "Criado em", "Obra", "Tarefa", "Local de entrega", "Status", "Itens"], stretch=2)
        self.tabela_pedidos.itemSelectionChanged.connect(self._mostrar_itens)
        self.paginacao_pedidos = BarraPaginacao()  # só aparece com mais de 30 pedidos
        self.paginacao_pedidos.mudou.connect(self._carregar_pedidos)
        self.resumo = QLabel()
        self.resumo.setObjectName("vazio")

        self.titulo_itens = QLabel("Itens do pedido")
        self.titulo_itens.setObjectName("subtitulo")
        self.tabela_itens = _tabela(["Produto", "Qtd.", "Un.", "Necessário até"], stretch=0)
        self.paginacao_itens = BarraPaginacao()  # só aparece com mais de 30 itens
        self.paginacao_itens.mudou.connect(self._desenhar_itens)

        em_cima = QWidget()
        lay_cima = QVBoxLayout(em_cima)
        lay_cima.setContentsMargins(0, 0, 0, 0)
        lay_cima.addLayout(barra)
        lay_cima.addWidget(self.tabela_pedidos, 1)
        lay_cima.addWidget(self.paginacao_pedidos)
        lay_cima.addWidget(self.resumo)
        embaixo = QWidget()
        lay_baixo = QVBoxLayout(embaixo)
        lay_baixo.setContentsMargins(0, 0, 0, 0)
        lay_baixo.addWidget(self.titulo_itens)
        lay_baixo.addWidget(self.tabela_itens, 1)
        lay_baixo.addWidget(self.paginacao_itens)
        divisor = QSplitter(Qt.Vertical)
        divisor.addWidget(em_cima)
        divisor.addWidget(embaixo)
        divisor.setStretchFactor(0, 3)
        divisor.setStretchFactor(1, 2)

        lay = QVBoxLayout(self)
        lay.addLayout(topo)
        lay.addWidget(self.rotulo_erro)
        lay.addWidget(divisor, 1)

        self.recarregar()

    def _fac(self) -> facedePedidoAPIInterface:
        """Facade de pedidos em uso.

        Returns:
            facedePedidoAPIInterface: o injetado ou `DIC.facede_pedido()`.
        """
        return self._facede or DIC.facede_pedido()

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe a mensagem de falha da API.

        Args:
            mensagem: texto a exibir.
        """
        self.rotulo_erro.setText(mensagem)
        self.rotulo_erro.show()

    def recarregar(self) -> None:
        """Atualiza a lista de status e a página atual de pedidos a partir da API.

        Em falha, mostra o erro e mantém o que estava na tela.

        Returns:
            None.
        """
        try:
            status = self._fac().status_dos_meus()
        except ApiError as e:
            self._mostrar_erro(f"Não foi possível carregar seus pedidos: {e.detalhe or e}")
            return
        escolhido = self.status.currentText()
        self.status.blockSignals(True)
        self.status.clear()
        self.status.addItems([TODOS, *status])
        if (i := self.status.findText(escolhido)) >= 0:
            self.status.setCurrentIndex(i)
        self.status.blockSignals(False)
        self._itens_cache.clear()
        self._carregar_pedidos()

    def _filtro_mudou(self) -> None:
        """O status escolhido mudou: volta à primeira página e consulta de novo."""
        self.paginacao_pedidos.voltar_ao_inicio()
        self._carregar_pedidos()

    def _carregar_pedidos(self) -> None:
        """Pede à API a página atual de pedidos (com o status escolhido) e a exibe.

        Se a página pedida ficou além do fim, volta para a última existente. Em falha mostra o
        erro e mantém a lista anterior.
        """
        status = self.status.currentText()
        status = None if status in ("", TODOS) else status
        barra = self.paginacao_pedidos
        for _tentativa in range(2):
            try:
                pedidos, total = self._fac().listar_meus_pagina(status, barra.tamanho, barra.inicio)
            except ApiError as e:
                self._mostrar_erro(f"Não foi possível carregar seus pedidos: {e.detalhe or e}")
                return
            if pedidos or total == 0 or barra.inicio == 0:
                break
            barra.definir_total(total)  # ajusta a página para a última existente
        self.rotulo_erro.hide()
        self.visiveis = pedidos
        barra.definir_total(total)
        self._desenhar_pedidos(total)

    def _desenhar_pedidos(self, total: int) -> None:
        """Desenha na tabela os pedidos da página atual e limpa a seleção (e os itens).

        Args:
            total: quantos pedidos casam com o filtro, somando todas as páginas.
        """
        pagina = self.visiveis
        t = self.tabela_pedidos
        t.blockSignals(True)
        t.setRowCount(len(pagina))
        for linha, p in enumerate(pagina):
            n = QTableWidgetItem(str(p.id))
            n.setData(Qt.UserRole, p.id)
            qtd = QTableWidgetItem(str(p.num_itens))
            qtd.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            for col, item in enumerate((
                n, QTableWidgetItem(formatar_data_hora(p.data_criacao)), QTableWidgetItem(p.obra),
                QTableWidgetItem(p.tarefa), QTableWidgetItem(p.local_entrega),
                QTableWidgetItem(p.status_atual), qtd,
            )):
                t.setItem(linha, col, item)
        t.blockSignals(False)
        t.clearSelection()
        if total:
            self.resumo.setText(f"{total} pedido(s)")
        elif self.status.currentText() in ("", TODOS):
            self.resumo.setText("Você ainda não fez nenhum pedido")
        else:
            self.resumo.setText("Nenhum pedido com esse status")
        self._mostrar_itens()

    def _mostrar_itens(self) -> None:
        """Mostra os itens do pedido selecionado (busca na API na primeira vez)."""
        linhas = self.tabela_pedidos.selectionModel().selectedRows()
        t = self.tabela_itens
        if not linhas:
            self._itens_exibidos = []
            self.paginacao_itens.definir_total(0, resetar=True)
            t.setRowCount(0)
            self.titulo_itens.setText("Itens do pedido — selecione um pedido acima")
            return
        pedido_id = self.tabela_pedidos.item(linhas[0].row(), 0).data(Qt.UserRole)
        itens = self._itens_cache.get(pedido_id)
        if itens is None:
            try:
                itens = self._fac().itens_do_pedido(pedido_id)
            except ApiError as e:
                self._mostrar_erro(f"Não foi possível carregar os itens do pedido {pedido_id}: {e.detalhe or e}")
                self._itens_exibidos = []
                self.paginacao_itens.definir_total(0, resetar=True)
                t.setRowCount(0)
                return
            self.rotulo_erro.hide()
            self._itens_cache[pedido_id] = itens
        self.titulo_itens.setText(f"Itens do pedido nº {pedido_id}")
        self._itens_exibidos = itens
        self.paginacao_itens.definir_total(len(itens), resetar=True)
        self._desenhar_itens()

    def _desenhar_itens(self) -> None:
        """Desenha na tabela só os itens da página atual do pedido selecionado."""
        t = self.tabela_itens
        pagina = self.paginacao_itens.fatia(self._itens_exibidos)
        t.setRowCount(len(pagina))
        for linha, it in enumerate(pagina):
            q = QTableWidgetItem(str(it.quant))
            q.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            t.setItem(linha, 0, QTableWidgetItem(it.produto))
            t.setItem(linha, 1, q)
            t.setItem(linha, 2, QTableWidgetItem(it.uni))
            t.setItem(linha, 3, QTableWidgetItem(it.data_necessidade.strftime("%d/%m/%Y")))


def main() -> None:
    """Abre a página "Meus pedidos" numa janela própria.

    Returns:
        None. Bloqueia até a janela ser fechada.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    janela = QMainWindow()
    janela.setWindowTitle("Sistema de Pedidos - Meus pedidos")
    janela.setCentralWidget(PaginaMeusPedidos())
    janela.resize(1100, 700)
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
