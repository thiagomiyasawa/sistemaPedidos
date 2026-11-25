"""Página do carrinho: itens escolhidos no catálogo, com remoção e finalização (PySide6).

O carrinho é o objeto compartilhado `DIC.carrinho()` (guardado no banco, via API); a tabela se
redesenha a cada `alterado` e falhas da API aparecem em vermelho. "Finalizar pedido" pede obra,
tarefa e local de entrega e só avisa o servidor para fechar o carrinho: é ele que monta o pedido
com as linhas do carrinho e as apaga.

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

from client.adapters.interfaces.adapterAPIInterface import ApiError  # noqa: E402
from client.componentes.barraPaginacao import BarraPaginacao  # noqa: E402
from client.DIC import DIC  # noqa: E402
from client.paginas.sisPedidos.paginaCarrinho.dialogoNovoPedido import (  # noqa: E402
    DialogoNovoPedido,
)
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
        tabela: Tabela com código, descrição, quantidade, unidade e data de necessidade (30 por
            página).
        paginacao: Barra de paginação da tabela.
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

        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(
            ["Código", "Descrição", "Qtd.", "Un.", "Necessário até"])
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tabela.verticalHeader().setVisible(False)
        cab = self.tabela.horizontalHeader()
        # O cabeçalho vem centralizado por padrão e as células, à esquerda: alinha os dois.
        cab.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tabela.horizontalHeaderItem(2).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Qtd.
        cab.setSectionResizeMode(1, QHeaderView.Stretch)
        cab.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cab.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        cab.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        cab.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.rotulo_erro = QLabel("")
        self.rotulo_erro.setStyleSheet("color: #c0392b;")
        self.rotulo_erro.setWordWrap(True)
        self.rotulo_erro.hide()
        self.resumo = QLabel()
        self.resumo.setObjectName("vazio")
        self.paginacao = BarraPaginacao()  # só aparece com mais de 30 linhas
        self.paginacao.mudou.connect(self.redesenhar)
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
        lay.addWidget(self.paginacao)
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
        self.paginacao.definir_total(len(itens))  # mantém a página (ajusta se encolheu)
        pagina = self.paginacao.fatia(itens)
        self.tabela.setRowCount(len(pagina))
        for linha, it in enumerate(pagina):
            q = QTableWidgetItem(str(it.quant))
            q.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            codigo = QTableWidgetItem(it.produto.codigo)
            codigo.setData(Qt.UserRole, it.id)  # identifica a linha do carrinho ao remover
            self.tabela.setItem(linha, 0, codigo)
            self.tabela.setItem(linha, 1, QTableWidgetItem(it.produto.descricao))
            self.tabela.setItem(linha, 2, q)
            self.tabela.setItem(linha, 3, QTableWidgetItem(it.uni))
            data = it.data_necessidade.strftime("%d/%m/%Y")
            self.tabela.setItem(linha, 4, QTableWidgetItem(data))
        n = len(itens)
        self.resumo.setText(f"{n} item(ns) distintos" if n else "Carrinho vazio")
        self.finalizar.setEnabled(n > 0)

    def _finalizar(self) -> None:
        """Pede os dados do pedido e manda o servidor fechar o carrinho.

        O servidor cria o pedido com as linhas do carrinho e as apaga; se a criação falhar
        (permissão, validação, rede), mostra o motivo e o carrinho continua como estava.
        """
        n_itens = len(self.carrinho.itens)
        dialogo = DialogoNovoPedido(n_itens, self)
        if dialogo.exec() != DialogoNovoPedido.Accepted:
            return
        dados = dialogo.dados()
        try:
            pedido_id = self.carrinho.finalizar(dados.obra, dados.tarefa, dados.local_entrega)
        except ApiError as e:
            QMessageBox.warning(self, "Pedido", f"Não foi possível criar o pedido:\n{e.detalhe or e}")
            return
        QMessageBox.information(self, "Pedido", f"Pedido nº {pedido_id} criado com {n_itens} item(ns).")


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
