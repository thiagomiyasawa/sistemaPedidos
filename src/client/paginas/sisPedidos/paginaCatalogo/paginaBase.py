"""Página de catálogo: consulta de produtos e adição de itens ao carrinho (PySide6).

Lista de produtos com busca por texto e filtro de categoria; o botão "Adicionar" de cada linha
abre um popup para informar quantidade, unidade e data de necessidade. Os itens vão para o
carrinho compartilhado (`DIC.carrinho()`), exibido na página do carrinho
(`sisPedidos/paginaCarrinho`).

A paginação é feita no servidor: a tela pede à API (`GET /produtos`) só os 30 produtos da página
atual, já filtrados por busca e categoria, e recebe o total para montar a barra de páginas. Se a
API falhar, a página mostra a mensagem de erro e mantém a lista anterior.

Execução:
    .venv/Scripts/python.exe "src/client/paginas/sisPedidos/paginaCatalogo/paginaBase.py"
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permite rodar o arquivo diretamente: coloca `src` no path (antes dos imports do projeto).
_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from PySide6.QtCore import Qt, QTimer, Signal  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractItemView,
    QApplication,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from client.adapters.interfaces.adapterAPIInterface import ApiError  # noqa: E402
from client.componentes.barraPaginacao import BarraPaginacao  # noqa: E402
from client.DIC import DIC  # noqa: E402
from client.facedes.interfaces.facedeProdutoAPIInterface import (  # noqa: E402
    facedeProdutoAPIInterface,
)
from client.paginas.sisPedidos.carrinho import Carrinho  # noqa: E402
from client.entidades.produto import Produto  # noqa: E402
from client.paginas.sisPedidos.paginaCatalogo.dialogoAdicionarItem import (  # noqa: E402
    DialogoAdicionarItem,
)

TODAS = "Todas"
ATRASO_BUSCA_MS = 300  # espera o usuário parar de digitar antes de consultar a API

ESTILO = """
QWidget { font-size: 10pt; }
#cabecalho { font-size: 15pt; font-weight: 700; }
#subtitulo { font-size: 11pt; font-weight: 600; }
#rotuloFiltro { font-size: 8pt; color: palette(placeholder-text); }
#vazio { color: palette(placeholder-text); }
"""


class PainelCatalogo(QWidget):
    """Busca, filtro de categoria, tabela da página atual, barra de páginas e botão de adicionar.

    O painel não conhece a API: quando busca, categoria ou página mudam ele emite `consultar`, e
    quem o hospeda lê `estado()`, consulta e devolve o resultado em `definir_pagina`.

    Signals:
        adicionar(Produto, int, str, date): emitido ao adicionar um produto com a
            quantidade, a unidade e a data de necessidade escolhidas.
        consultar(): emitido quando é preciso buscar de novo a página (filtro ou página mudou).

    Attributes:
        visiveis: Produtos da página atual.
        paginacao: Barra de páginas (alimentada com o total devolvido pela API).
    """

    adicionar = Signal(object, int, str, object)
    consultar = Signal()

    def __init__(self) -> None:
        """Monta filtros, tabela e barra de páginas (vazios até `definir_pagina`)."""
        super().__init__()
        self.visiveis: list[Produto] = []

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar por código ou descrição...")
        self.busca.setClearButtonEnabled(True)
        self._timer_busca = QTimer(self)
        self._timer_busca.setSingleShot(True)
        self._timer_busca.setInterval(ATRASO_BUSCA_MS)
        self._timer_busca.timeout.connect(self._filtro_mudou)
        self.busca.textChanged.connect(lambda _t: self._timer_busca.start())
        self.busca.returnPressed.connect(self._busca_agora)

        self.categoria = QComboBox()
        self.categoria.addItem(TODAS)
        self.categoria.currentIndexChanged.connect(self._filtro_mudou)

        filtros = QHBoxLayout()
        filtros.addWidget(self._com_rotulo("Busca", self.busca), 1)
        filtros.addWidget(self._com_rotulo("Categoria", self.categoria))

        self.tabela = QTableWidget(0, 4)
        self.tabela.setHorizontalHeaderLabels(["Código", "Descrição", "Categoria", ""])
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela.verticalHeader().setVisible(False)
        cab = self.tabela.horizontalHeader()
        cab.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # igual ao conteúdo das células
        cab.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in (0, 2, 3):
            cab.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.contagem = QLabel()
        self.contagem.setObjectName("vazio")
        self.paginacao = BarraPaginacao()  # só aparece com mais de 30 produtos
        self.paginacao.mudou.connect(self.consultar)

        titulo = QLabel("Catálogo")
        titulo.setObjectName("subtitulo")
        lay = QVBoxLayout(self)
        lay.addWidget(titulo)
        lay.addLayout(filtros)
        lay.addWidget(self.tabela, 1)
        lay.addWidget(self.paginacao)
        lay.addWidget(self.contagem)

    @staticmethod
    def _com_rotulo(rotulo: str, w: QWidget) -> QWidget:
        """Põe um rótulo pequeno sobre o controle.

        Args:
            rotulo: Texto do rótulo.
            w: Controle.

        Returns:
            Contêiner com rótulo + controle.
        """
        caixa = QWidget()
        box = QVBoxLayout(caixa)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        lbl = QLabel(rotulo)
        lbl.setObjectName("rotuloFiltro")
        box.addWidget(lbl)
        box.addWidget(w)
        return caixa

    def _busca_agora(self) -> None:
        """Enter no campo de busca: consulta já, sem esperar o atraso."""
        self._timer_busca.stop()
        self._filtro_mudou()

    def _filtro_mudou(self) -> None:
        """Busca ou categoria mudaram: volta à primeira página e pede nova consulta."""
        self._timer_busca.stop()
        self.paginacao.voltar_ao_inicio()
        self.consultar.emit()

    def estado(self) -> tuple[str | None, str | None, int, int]:
        """Parâmetros da consulta atual.

        Returns:
            tuple: `(busca, categoria, limit, offset)`; busca e categoria são None quando vazias
            ou "Todas".
        """
        busca = self.busca.text().strip() or None
        categoria = self.categoria.currentText()
        return (busca, None if categoria in ("", TODAS) else categoria,
                self.paginacao.tamanho, self.paginacao.inicio)

    def definir_categorias(self, categorias: list[str]) -> None:
        """Atualiza a lista do filtro de categoria, mantendo a escolhida se ainda existir.

        Args:
            categorias: categorias vindas da API.
        """
        escolhida = self.categoria.currentText()
        self.categoria.blockSignals(True)
        self.categoria.clear()
        self.categoria.addItems([TODAS, *categorias])
        if (i := self.categoria.findText(escolhida)) >= 0:
            self.categoria.setCurrentIndex(i)
        self.categoria.blockSignals(False)

    def definir_pagina(self, produtos: list[Produto], total: int) -> None:
        """Mostra os produtos da página devolvida pela API.

        Args:
            produtos: produtos da página atual.
            total: quantos produtos casam com o filtro, somando todas as páginas.
        """
        self.visiveis = produtos
        self.paginacao.definir_total(total)
        self.tabela.setRowCount(len(produtos))
        for linha, p in enumerate(produtos):
            for col, valor in enumerate((p.codigo, p.descricao, p.categoria)):
                self.tabela.setItem(linha, col, QTableWidgetItem(valor))
            btn = QPushButton("Adicionar")
            btn.clicked.connect(lambda _=False, prod=p: self._adicionar(prod))
            self.tabela.setCellWidget(linha, 3, btn)
        self.contagem.setText(f"{total} produto(s)")

    def _adicionar(self, produto: Produto) -> None:
        """Abre o popup de detalhes e, se confirmado, emite `adicionar`.

        Args:
            produto: Produto escolhido.
        """
        dialogo = DialogoAdicionarItem(produto, self)
        if dialogo.exec() == DialogoAdicionarItem.Accepted and dialogo.unidade():
            self.adicionar.emit(
                produto, dialogo.quantidade(), dialogo.unidade(), dialogo.data_necessidade())


class PaginaCatalogo(QWidget):
    """Página do catálogo; os produtos adicionados vão para o carrinho compartilhado.

    Attributes:
        catalogo: Painel com busca, filtro e tabela de produtos.
        carrinho: Carrinho que recebe os itens adicionados.
        rotulo_erro: Mensagem de falha ao carregar o catálogo.
        rotulo_carrinho: Resumo de quantos itens há no carrinho.
    """

    TITULO = "Catálogo de Produtos"

    def __init__(self, facede: facedeProdutoAPIInterface | None = None,
                 carrinho: Carrinho | None = None) -> None:
        """Monta cabeçalho e o painel do catálogo e carrega a primeira página.

        Args:
            facede: facade de produtos; se None usa `DIC.facede_produto()`.
            carrinho: carrinho que recebe os itens; se None usa `DIC.carrinho()`.
        """
        super().__init__()
        self.setStyleSheet(ESTILO)
        self._facede = facede
        self.carrinho = carrinho or DIC.carrinho()
        self.catalogo = PainelCatalogo()
        self.catalogo.adicionar.connect(self.carrinho.adicionar)
        self.catalogo.consultar.connect(self.carregar_pagina)
        self.rotulo_carrinho = QLabel()
        self.rotulo_carrinho.setObjectName("vazio")
        self.carrinho.alterado.connect(self._atualizar_resumo_carrinho)
        self.carrinho.falhou.connect(self._erro_carrinho)
        self._atualizar_resumo_carrinho()

        cab = QLabel(self.TITULO)
        cab.setObjectName("cabecalho")
        recarregar = QPushButton("Recarregar")
        recarregar.clicked.connect(self.recarregar)
        self.rotulo_erro = QLabel("")
        self.rotulo_erro.setStyleSheet("color: #c0392b;")
        self.rotulo_erro.setWordWrap(True)
        self.rotulo_erro.hide()
        topo = QHBoxLayout()
        topo.addWidget(cab)
        topo.addStretch(1)
        topo.addWidget(recarregar)

        lay = QVBoxLayout(self)
        lay.addLayout(topo)
        lay.addWidget(self.rotulo_erro)
        lay.addWidget(self.catalogo, 1)
        lay.addWidget(self.rotulo_carrinho)
        self.recarregar()
        self.carrinho.recarregar()  # traz o carrinho do usuário guardado no banco

    def _fac(self) -> facedeProdutoAPIInterface:
        """Facade de produtos em uso.

        Returns:
            facedeProdutoAPIInterface: o injetado ou `DIC.facede_produto()`.
        """
        return self._facede or DIC.facede_produto()

    def _erro_carrinho(self, mensagem: str) -> None:
        """Mostra, no resumo do carrinho, a falha ao acessá-lo na API.

        Args:
            mensagem: texto a exibir.
        """
        self.rotulo_carrinho.setStyleSheet("color: #c0392b;")
        self.rotulo_carrinho.setText(f"Erro no carrinho: {mensagem}")

    def _atualizar_resumo_carrinho(self) -> None:
        """Atualiza o texto com a quantidade de itens distintos no carrinho."""
        n = len(self.carrinho.itens)
        self.rotulo_carrinho.setStyleSheet("")
        self.rotulo_carrinho.setText(f"{n} item(ns) no carrinho" if n else "Carrinho vazio")

    def recarregar(self) -> None:
        """Atualiza as categorias do filtro e a página atual a partir da API.

        Em falha mostra o erro e mantém o que estava na tela.

        Returns:
            None.
        """
        try:
            self.catalogo.definir_categorias(self._fac().categorias())
        except ApiError as e:
            self._mostrar_erro(e)
            return
        self.carregar_pagina()

    def carregar_pagina(self) -> None:
        """Pede à API a página atual (com a busca e a categoria escolhidas) e a exibe.

        Se a página pedida ficou além do fim (itens saíram do catálogo), volta para a última.

        Returns:
            None. Em falha mostra o erro e mantém a lista anterior.
        """
        for _tentativa in range(2):
            busca, categoria, limit, offset = self.catalogo.estado()
            try:
                produtos, total = self._fac().listar_pagina(busca, categoria, limit, offset)
            except ApiError as e:
                self._mostrar_erro(e)
                return
            paginacao = self.catalogo.paginacao
            if produtos or total == 0 or offset == 0:
                break
            paginacao.definir_total(total)  # ajusta a página para a última existente
        self.rotulo_erro.hide()
        self.catalogo.definir_pagina(produtos, total)

    def _mostrar_erro(self, e: ApiError) -> None:
        """Exibe a falha ao carregar o catálogo.

        Args:
            e: erro da API.
        """
        self.rotulo_erro.setText(f"Não foi possível carregar o catálogo: {e.detalhe or e}")
        self.rotulo_erro.show()


class JanelaPrincipal(QMainWindow):
    """Janela que hospeda a página do catálogo."""

    def __init__(self, pagina: QWidget, titulo: str) -> None:
        """Configura título, widget central e tamanho inicial.

        Args:
            pagina: Widget central.
            titulo: Título da janela.
        """
        super().__init__()
        self.setWindowTitle(titulo)
        self.setCentralWidget(pagina)
        self.resize(1200, 700)


def main() -> None:
    """Abre a página do catálogo em uma janela própria."""
    app = QApplication.instance() or QApplication(sys.argv)
    janela = JanelaPrincipal(PaginaCatalogo(), "Sistema de Pedidos - Catálogo")
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
