"""Página de catálogo: consulta de produtos e adição de itens ao carrinho (PySide6).

Lista de produtos com busca por texto e filtro de categoria; cada linha tem quantidade e botão
"Adicionar". Os itens vão para o carrinho compartilhado (`DIC.carrinho()`), exibido na página
do carrinho (`sisPedidos/paginaCarrinho`).
O catálogo vem da API (`GET /produtos`) pelo facade de produtos. Se a API falhar, a página
mostra a mensagem de erro no lugar da lista.

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

from PySide6.QtCore import Qt, Signal  # noqa: E402
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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from client.adapters.interfaces.adapterAPIInterface import ApiError  # noqa: E402
from client.DIC import DIC  # noqa: E402
from client.paginas.sisPedidos.acessoServidor.interfaces.facedeProdutoAPIInterface import (  # noqa: E402
    facedeProdutoAPIInterface,
)
from client.paginas.sisPedidos.carrinho import Carrinho  # noqa: E402
from client.paginas.sisPedidos.entidades.produto import Produto  # noqa: E402

TODAS = "Todas"

ESTILO = """
QWidget { font-size: 10pt; }
#cabecalho { font-size: 15pt; font-weight: 700; }
#subtitulo { font-size: 11pt; font-weight: 600; }
#rotuloFiltro { font-size: 8pt; color: palette(placeholder-text); }
#vazio { color: palette(placeholder-text); }
"""


def carregar_catalogo(facede: facedeProdutoAPIInterface | None = None) -> list[Produto]:
    """Obtém os produtos do catálogo pela API (facade de produtos).

    Args:
        facede: facade de produtos; se None usa `DIC.facede_produto()`.

    Returns:
        Lista de `Produto`.

    Raises:
        ApiError: em falha de comunicação com a API.
    """
    return (facede or DIC.facede_produto()).listar()


class PainelCatalogo(QWidget):
    """Lista de produtos com busca, filtro de categoria e botão de adicionar.

    Signals:
        adicionar(Produto, int): emitido ao adicionar um produto com a quantidade escolhida.
    """

    adicionar = Signal(object, int)

    def __init__(self, produtos: list[Produto]) -> None:
        """Monta filtros e tabela.

        Args:
            produtos: Produtos do catálogo.
        """
        super().__init__()
        self.produtos = produtos
        self.visiveis: list[Produto] = []

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar por código ou descrição...")
        self.busca.setClearButtonEnabled(True)
        self.busca.textChanged.connect(self.atualizar)

        self.categoria = QComboBox()
        self.categoria.currentIndexChanged.connect(self.atualizar)

        filtros = QHBoxLayout()
        filtros.addWidget(self._com_rotulo("Busca", self.busca), 1)
        filtros.addWidget(self._com_rotulo("Categoria", self.categoria))

        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["Código", "Descrição", "Categoria", "Qtd.", ""])
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela.verticalHeader().setVisible(False)
        cab = self.tabela.horizontalHeader()
        cab.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in (0, 2, 3, 4):
            cab.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.contagem = QLabel()
        self.contagem.setObjectName("vazio")

        titulo = QLabel("Catálogo")
        titulo.setObjectName("subtitulo")
        lay = QVBoxLayout(self)
        lay.addWidget(titulo)
        lay.addLayout(filtros)
        lay.addWidget(self.tabela, 1)
        lay.addWidget(self.contagem)

        self.definir_produtos(produtos)

    def definir_produtos(self, produtos: list[Produto]) -> None:
        """Troca o catálogo exibido, mantendo a categoria escolhida se ainda existir.

        Args:
            produtos: Novos produtos do catálogo.
        """
        self.produtos = produtos
        escolhida = self.categoria.currentText()
        self.categoria.blockSignals(True)
        self.categoria.clear()
        self.categoria.addItems([TODAS, *sorted({p.categoria for p in produtos if p.categoria})])
        if (i := self.categoria.findText(escolhida)) >= 0:
            self.categoria.setCurrentIndex(i)
        self.categoria.blockSignals(False)
        self.atualizar()

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

    def atualizar(self) -> None:
        """Refiltra os produtos pela busca e categoria e redesenha a tabela."""
        texto = self.busca.text().strip().casefold()
        cat = self.categoria.currentText()
        self.visiveis = [
            p for p in self.produtos
            if (cat == TODAS or p.categoria == cat)
            and (not texto or texto in p.codigo.casefold() or texto in p.descricao.casefold())
        ]
        self.tabela.setRowCount(len(self.visiveis))
        for linha, p in enumerate(self.visiveis):
            for col, valor in enumerate((p.codigo, p.descricao, p.categoria)):
                self.tabela.setItem(linha, col, QTableWidgetItem(valor))
            spin = QSpinBox()
            spin.setRange(1, 99999)
            btn = QPushButton("Adicionar")
            btn.clicked.connect(lambda _=False, prod=p, s=spin: self._adicionar(prod, s))
            self.tabela.setCellWidget(linha, 3, spin)
            self.tabela.setCellWidget(linha, 4, btn)
        self.contagem.setText(f"{len(self.visiveis)} de {len(self.produtos)} produtos")

    def _adicionar(self, produto: Produto, spin: QSpinBox) -> None:
        """Emite `adicionar` e volta a quantidade para 1.

        Args:
            produto: Produto escolhido.
            spin: Campo de quantidade da linha.
        """
        self.adicionar.emit(produto, spin.value())
        spin.setValue(1)


class PaginaCatalogo(QWidget):
    """Página do catálogo; os produtos adicionados vão para o carrinho compartilhado.

    Attributes:
        catalogo: Painel com busca, filtro e tabela de produtos.
        carrinho: Carrinho que recebe os itens adicionados.
        rotulo_erro: Mensagem de falha ao carregar o catálogo.
        rotulo_carrinho: Resumo de quantos itens há no carrinho.
    """

    TITULO = "Catálogo de Produtos"

    def __init__(self, produtos: list[Produto] | None = None,
                 facede: facedeProdutoAPIInterface | None = None,
                 carrinho: Carrinho | None = None) -> None:
        """Monta cabeçalho e o painel do catálogo e carrega os produtos.

        Args:
            produtos: Catálogo a exibir; se None, é obtido da API por `recarregar()`.
            facede: facade de produtos; se None usa `DIC.facede_produto()`.
            carrinho: carrinho que recebe os itens; se None usa `DIC.carrinho()`.
        """
        super().__init__()
        self.setStyleSheet(ESTILO)
        self._facede = facede
        self.carrinho = carrinho or DIC.carrinho()
        self.catalogo = PainelCatalogo(produtos or [])
        self.catalogo.adicionar.connect(self.carrinho.adicionar)
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
        if produtos is None:
            self.recarregar()
        self.carrinho.recarregar()  # traz o carrinho do usuário guardado no banco

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
        """Busca o catálogo na API e atualiza a lista; em falha mostra o erro e mantém a lista.

        Returns:
            None.
        """
        try:
            produtos = carregar_catalogo(self._facede)
        except ApiError as e:
            self.rotulo_erro.setText(f"Não foi possível carregar o catálogo: {e.detalhe or e}")
            self.rotulo_erro.show()
            return
        self.rotulo_erro.hide()
        self.catalogo.definir_produtos(produtos)


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
