"""Página de catálogo: consulta de produtos e adição de itens ao carrinho (PySide6).

À esquerda, a lista de produtos com busca por texto e filtro de categoria; cada linha tem
quantidade e botão "Adicionar". À direita, o carrinho (editável: remover item, limpar).
O catálogo vem de `carregar_catalogo()`, hoje uma lista de exemplo: troque essa função
pela consulta real (API/banco) sem mexer na tela.

Execução:
    .venv\\Scripts\\python.exe "src/sisPedidos/paginaCatalogo/paginaBase.py"
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Permite rodar o arquivo diretamente: coloca `src` no path (antes dos imports do projeto).
_SRC = Path(__file__).resolve().parents[2]
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
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

TODAS = "Todas"

ESTILO = """
QWidget { font-size: 10pt; }
#cabecalho { font-size: 15pt; font-weight: 700; }
#subtitulo { font-size: 11pt; font-weight: 600; }
#rotuloFiltro { font-size: 8pt; color: palette(placeholder-text); }
#vazio { color: palette(placeholder-text); }
"""


@dataclass(frozen=True)
class Produto:
    """Produto do catálogo.

    Attributes:
        codigo: Código único do produto.
        descricao: Nome/descrição exibidos.
        categoria: Categoria para filtro.
        unidade: Unidade de medida (un, m, kg...).
    """

    codigo: str
    descricao: str
    categoria: str
    unidade: str


@dataclass
class ItemCarrinho:
    """Item no carrinho: produto e quantidade acumulada."""

    produto: Produto
    quant: int


def carregar_catalogo() -> list[Produto]:
    """Obtém os produtos do catálogo.

    Hoje devolve dados de exemplo; substitua pela consulta real (API ou banco).

    Returns:
        Lista de `Produto`.
    """
    return [
        Produto("EL-001", "Cabo flexível 2,5 mm² (rolo 100 m)", "Elétrica", "rolo"),
        Produto("EL-002", "Disjuntor monopolar 20 A", "Elétrica", "un"),
        Produto("EL-003", "Eletroduto corrugado 3/4\"", "Elétrica", "m"),
        Produto("HI-001", "Tubo PVC soldável 25 mm (barra 6 m)", "Hidráulica", "un"),
        Produto("HI-002", "Registro de esfera 3/4\"", "Hidráulica", "un"),
        Produto("HI-003", "Cola para PVC 175 g", "Hidráulica", "un"),
        Produto("CV-001", "Cimento CP-II 50 kg", "Civil", "saco"),
        Produto("CV-002", "Areia média", "Civil", "m³"),
        Produto("CV-003", "Vergalhão CA-50 10 mm (barra 12 m)", "Civil", "un"),
        Produto("EP-001", "Capacete de segurança", "EPI", "un"),
        Produto("EP-002", "Luva de raspa", "EPI", "par"),
        Produto("EP-003", "Óculos de proteção", "EPI", "un"),
    ]


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
        self.categoria.addItems([TODAS, *sorted({p.categoria for p in produtos})])
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
            spin.setSuffix(f" {p.unidade}")
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


class PainelCarrinho(QWidget):
    """Carrinho: lista os itens, soma quantidades repetidas e permite remover/limpar."""

    def __init__(self) -> None:
        """Monta a tabela do carrinho e os botões."""
        super().__init__()
        self.itens: dict[str, ItemCarrinho] = {}

        self.tabela = QTableWidget(0, 3)
        self.tabela.setHorizontalHeaderLabels(["Código", "Descrição", "Qtd."])
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tabela.verticalHeader().setVisible(False)
        cab = self.tabela.horizontalHeader()
        cab.setSectionResizeMode(1, QHeaderView.Stretch)
        cab.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cab.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.resumo = QLabel()
        self.resumo.setObjectName("vazio")
        remover = QPushButton("Remover selecionados")
        remover.clicked.connect(self.remover_selecionados)
        limpar = QPushButton("Limpar")
        limpar.clicked.connect(self.limpar)
        self.finalizar = QPushButton("Finalizar pedido")
        self.finalizar.clicked.connect(self._finalizar)

        botoes = QHBoxLayout()
        botoes.addWidget(remover)
        botoes.addWidget(limpar)

        titulo = QLabel("Carrinho")
        titulo.setObjectName("subtitulo")
        lay = QVBoxLayout(self)
        lay.addWidget(titulo)
        lay.addWidget(self.tabela, 1)
        lay.addWidget(self.resumo)
        lay.addLayout(botoes)
        lay.addWidget(self.finalizar)
        self.redesenhar()

    def adicionar(self, produto: Produto, quant: int) -> None:
        """Adiciona o produto ao carrinho, somando se já existir.

        Args:
            produto: Produto a adicionar.
            quant: Quantidade (positiva).
        """
        if produto.codigo in self.itens:
            self.itens[produto.codigo].quant += quant
        else:
            self.itens[produto.codigo] = ItemCarrinho(produto, quant)
        self.redesenhar()

    def remover_selecionados(self) -> None:
        """Remove do carrinho as linhas selecionadas."""
        for idx in self.tabela.selectionModel().selectedRows():
            codigo = self.tabela.item(idx.row(), 0).text()
            self.itens.pop(codigo, None)
        self.redesenhar()

    def limpar(self) -> None:
        """Esvazia o carrinho."""
        self.itens.clear()
        self.redesenhar()

    def redesenhar(self) -> None:
        """Atualiza a tabela, o resumo e o estado do botão de finalizar."""
        self.tabela.setRowCount(len(self.itens))
        for linha, it in enumerate(self.itens.values()):
            q = QTableWidgetItem(f"{it.quant} {it.produto.unidade}")
            q.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(linha, 0, QTableWidgetItem(it.produto.codigo))
            self.tabela.setItem(linha, 1, QTableWidgetItem(it.produto.descricao))
            self.tabela.setItem(linha, 2, q)
        n = len(self.itens)
        self.resumo.setText(f"{n} item(ns) distintos" if n else "Carrinho vazio")
        self.finalizar.setEnabled(n > 0)

    def _finalizar(self) -> None:
        """Ponto de integração com a criação do pedido (ainda não implementado).

        Hoje só confirma os itens; ligue aqui ao `facede_pedido.criar_pedido`/`adicionar_item`.
        """
        QMessageBox.information(self, "Pedido", f"{len(self.itens)} item(ns) prontos para o pedido.")


class PaginaCatalogo(QWidget):
    """Página completa: catálogo à esquerda, carrinho à direita."""

    TITULO = "Catálogo de Produtos"

    def __init__(self, produtos: list[Produto] | None = None) -> None:
        """Monta cabeçalho e os dois painéis.

        Args:
            produtos: Catálogo a exibir; se None, usa `carregar_catalogo()`.
        """
        super().__init__()
        self.setStyleSheet(ESTILO)
        self.catalogo = PainelCatalogo(produtos if produtos is not None else carregar_catalogo())
        self.carrinho = PainelCarrinho()
        self.catalogo.adicionar.connect(self.carrinho.adicionar)

        cab = QLabel(self.TITULO)
        cab.setObjectName("cabecalho")
        divisor = QSplitter(Qt.Horizontal)
        divisor.addWidget(self.catalogo)
        divisor.addWidget(self.carrinho)
        divisor.setStretchFactor(0, 3)
        divisor.setStretchFactor(1, 2)

        lay = QVBoxLayout(self)
        lay.addWidget(cab)
        lay.addWidget(divisor, 1)


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
