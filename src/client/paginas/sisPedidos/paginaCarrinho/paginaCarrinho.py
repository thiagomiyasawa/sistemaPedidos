"""Página do carrinho: itens escolhidos no catálogo, com remoção e finalização (PySide6).

O carrinho é o objeto compartilhado `DIC.carrinho()` (guardado no banco, via API); a tabela se
redesenha a cada `alterado` e falhas da API aparecem em vermelho.

Execução:
    .venv/Scripts/python.exe "src/client/paginas/sisPedidos/paginaCarrinho/paginaCarrinho.py"
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permite rodar o arquivo diretamente: coloca `src` no path (antes dos imports do projeto).
_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from client.DIC import DIC  # noqa: E402
from client.paginas.sisPedidos.carrinho import Carrinho  # noqa: E402

ESTILO = """
QWidget { font-size: 10pt; }
#cabecalho { font-size: 15pt; font-weight: 700; }
#vazio { color: palette(placeholder-text); }
"""


class PaginaCarrinho(QWidget):
    """Tabela do carrinho com remover selecionados, limpar e finalizar.

    Attributes:
        carrinho: Carrinho exibido (compartilhado com o catálogo).
        tabela: Tabela com código, descrição e quantidade.
        rotulo_erro: Mensagem da última falha ao acessar a API.
        finalizar: Botão de finalizar o pedido (desabilitado com o carrinho vazio).
    """

    TITULO = "Carrinho"

    def __init__(self, carrinho: Carrinho | None = None) -> None:
        """Monta a tabela e os botões e passa a acompanhar o carrinho.

        Args:
            carrinho: Carrinho a exibir; se None usa `DIC.carrinho()`.
        """
        super().__init__()
        self.setStyleSheet(ESTILO)
        self.carrinho = carrinho or DIC.carrinho()

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

        self.rotulo_erro = QLabel("")
        self.rotulo_erro.setStyleSheet("color: #c0392b;")
        self.rotulo_erro.setWordWrap(True)
        self.rotulo_erro.hide()
        self.resumo = QLabel()
        self.resumo.setObjectName("vazio")
        remover = QPushButton("Remover selecionados")
        remover.clicked.connect(self.remover_selecionados)
        limpar = QPushButton("Limpar")
        limpar.clicked.connect(self.carrinho.limpar)
        self.finalizar = QPushButton("Finalizar pedido")
        self.finalizar.clicked.connect(self._finalizar)

        botoes = QHBoxLayout()
        botoes.addWidget(remover)
        botoes.addWidget(limpar)

        titulo = QLabel(self.TITULO)
        titulo.setObjectName("cabecalho")
        lay = QVBoxLayout(self)
        lay.addWidget(titulo)
        lay.addWidget(self.rotulo_erro)
        lay.addWidget(self.tabela, 1)
        lay.addWidget(self.resumo)
        lay.addLayout(botoes)
        lay.addWidget(self.finalizar)

        self.carrinho.alterado.connect(self.redesenhar)
        self.carrinho.falhou.connect(self._mostrar_erro)
        self.redesenhar()
        self.carrinho.recarregar()  # traz o carrinho do usuário guardado no banco

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe a mensagem de falha da API.

        Args:
            mensagem: texto a exibir.
        """
        self.rotulo_erro.setText(f"Erro no carrinho: {mensagem}")
        self.rotulo_erro.show()

    def remover_selecionados(self) -> None:
        """Remove do carrinho as linhas selecionadas."""
        ids = [self.tabela.item(idx.row(), 0).data(Qt.UserRole)
               for idx in self.tabela.selectionModel().selectedRows()]
        self.carrinho.remover(ids)

    def redesenhar(self) -> None:
        """Atualiza a tabela, o resumo e o estado do botão de finalizar."""
        self.rotulo_erro.hide()
        itens = list(self.carrinho.itens.values())
        self.tabela.setRowCount(len(itens))
        for linha, it in enumerate(itens):
            q = QTableWidgetItem(str(it.quant))
            q.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            codigo = QTableWidgetItem(it.produto.codigo)
            codigo.setData(Qt.UserRole, it.produto.id)  # identifica a linha ao remover
            self.tabela.setItem(linha, 0, codigo)
            self.tabela.setItem(linha, 1, QTableWidgetItem(it.produto.descricao))
            self.tabela.setItem(linha, 2, q)
        n = len(itens)
        self.resumo.setText(f"{n} item(ns) distintos" if n else "Carrinho vazio")
        self.finalizar.setEnabled(n > 0)

    def _finalizar(self) -> None:
        """Ponto de integração com a criação do pedido (ainda não implementado).

        Hoje só confirma os itens; ligue aqui ao `facede_pedido.criar_pedido`/`adicionar_item`.
        """
        QMessageBox.information(
            self, "Pedido", f"{len(self.carrinho.itens)} item(ns) prontos para o pedido.")


def main() -> None:
    """Abre a página do carrinho em uma janela própria (carrinho vazio, sem catálogo).

    Returns:
        None. Bloqueia até a janela ser fechada.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    janela = QMainWindow()
    janela.setWindowTitle("Sistema de Pedidos - Carrinho")
    janela.setCentralWidget(PaginaCarrinho())
    janela.resize(800, 600)
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
