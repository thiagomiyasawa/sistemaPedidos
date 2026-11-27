"""Página de menu (PySide6): barra lateral com os módulos e, ao lado, a página selecionada.

Cada página é criada na primeira vez que o item é escolhido (as de KPI consultam a API ao
nascer) e depois reaproveitada. As páginas usam o adapter compartilhado (`DIC.api`), que recebe
a chave de API no login. O login redireciona para cá.
Execução (sem login; a chave deve estar em `MONITORKPI_API_KEY`):
    .venv/Scripts/python.exe "src/client/paginas/sistemaMenu/paginaMenu.py"
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

# Permite rodar o arquivo diretamente: coloca `src` no path (antes dos imports do projeto).
_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from PySide6.QtCore import Qt, Signal  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

ESTILO_MENU = """
#barraLateral { background: palette(alternate-base); border-right: 1px solid palette(mid); }
#tituloMenu { font-size: 14pt; font-weight: 700; padding: 4px 8px 12px 8px; }
#botaoMenu { padding: 10px 12px; text-align: left; border: none; border-radius: 6px;
             background: transparent; }
#botaoMenu:hover { background: palette(midlight); }
#botaoMenu:checked { background: palette(highlight); color: palette(highlighted-text);
                     font-weight: 600; }
#erroMenu { color: #c0392b; padding: 24px; }
#botaoSair { padding: 10px 12px; text-align: left; border: 1px solid palette(mid);
             border-radius: 6px; background: transparent; }
#botaoSair:hover { background: palette(midlight); }
"""


def _pagina_kpi_geral() -> QWidget:
    """Cria a página dos KPIs de pedidos (visão geral).

    Returns:
        A página, pronta para ser colocada na área de conteúdo.
    """
    from client.paginas.monitorkpi.paginas.paginasPedidos.paginaPedidosGeral.paginaGeral import (
        PaginaKPIPedidos,
    )

    return PaginaKPIPedidos()


def _pagina_kpi_obra() -> QWidget:
    """Cria a página dos KPIs de pedidos por obra.

    Returns:
        A página, pronta para ser colocada na área de conteúdo.
    """
    from client.paginas.monitorkpi.paginas.paginasPedidos.paginaPedidosObra.paginaObra import (
        PaginaKPIPedidosObra,
    )

    return PaginaKPIPedidosObra()


def _pagina_catalogo() -> QWidget:
    """Cria a página do catálogo de produtos (carrega os produtos da API).

    Returns:
        A página, pronta para ser colocada na área de conteúdo.
    """
    from client.paginas.sisPedidos.paginaCatalogo.paginaBase import PaginaCatalogo

    return PaginaCatalogo()


def _pagina_carrinho() -> QWidget:
    """Cria a página do carrinho (itens escolhidos no catálogo).

    Returns:
        A página, pronta para ser colocada na área de conteúdo.
    """
    from client.paginas.sisPedidos.paginaCarrinho.paginaCarrinho import PaginaCarrinho

    return PaginaCarrinho()


def _pagina_meus_pedidos() -> QWidget:
    """Cria a página com os pedidos do usuário e seus itens.

    Returns:
        A página, pronta para ser colocada na área de conteúdo.
    """
    from client.paginas.sisPedidos.paginaMeusPedidos.paginaMeusPedidos import PaginaMeusPedidos

    return PaginaMeusPedidos()


# (título do item, fábrica da página). Para um módulo novo, basta acrescentar uma linha.
ENTRADAS: list[tuple[str, Callable[[], QWidget]]] = [
    ("KPIs - Geral", _pagina_kpi_geral),
    ("KPIs - Por obra", _pagina_kpi_obra),
    ("Catálogo", _pagina_catalogo),
    ("Carrinho", _pagina_carrinho),
    ("Meus pedidos", _pagina_meus_pedidos),
]


class PaginaMenu(QWidget):
    """Barra lateral de navegação + área de conteúdo com a página selecionada.

    O menu não encerra a sessão: o botão "Sair" só emite `sair`, e quem hospeda o menu faz o
    logout e troca a tela (ver `main` em `sistemaLogin/paginaLogin.py`).

    Signals:
        sair(): emitido quando o usuário clica em "Sair".

    Attributes:
        pilha: Área de conteúdo; guarda as páginas já criadas.
        botoes: Botões da barra lateral, na ordem de `entradas`.
        botao_sair: Botão "Sair", no pé da barra lateral.
    """

    sair = Signal()

    def __init__(self, entradas: list[tuple[str, Callable[[], QWidget]]] | None = None) -> None:
        """Monta a barra lateral e seleciona o primeiro item.

        Args:
            entradas: Lista `(título, fábrica da página)`; se None usa `ENTRADAS`.

        Returns:
            None.
        """
        super().__init__()
        self.setStyleSheet(ESTILO_MENU)
        self._entradas = list(entradas if entradas is not None else ENTRADAS)
        self._paginas: dict[int, QWidget] = {}  # índice da entrada -> página já criada

        titulo = QLabel("Monitor KPI")
        titulo.setObjectName("tituloMenu")

        barra = QFrame()
        barra.setObjectName("barraLateral")
        barra.setFixedWidth(220)
        lay_barra = QVBoxLayout(barra)
        lay_barra.setContentsMargins(10, 14, 10, 14)
        lay_barra.setSpacing(4)
        lay_barra.addWidget(titulo)

        grupo = QButtonGroup(self)
        grupo.setExclusive(True)
        self.botoes: list[QPushButton] = []
        for i, (nome, _fabrica) in enumerate(self._entradas):
            botao = QPushButton(nome)
            botao.setObjectName("botaoMenu")
            botao.setCheckable(True)
            botao.setCursor(Qt.PointingHandCursor)
            botao.clicked.connect(lambda _=False, idx=i: self.selecionar(idx))
            grupo.addButton(botao)
            lay_barra.addWidget(botao)
            self.botoes.append(botao)
        lay_barra.addStretch(1)
        self.botao_sair = QPushButton("Sair")
        self.botao_sair.setObjectName("botaoSair")
        self.botao_sair.setCursor(Qt.PointingHandCursor)
        self.botao_sair.clicked.connect(self.sair)
        lay_barra.addWidget(self.botao_sair)

        self.pilha = QStackedWidget()

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(barra)
        raiz.addWidget(self.pilha, 1)

        if self._entradas:
            self.selecionar(0)

    def selecionar(self, indice: int) -> None:
        """Mostra a página da entrada, criando-a na primeira vez.

        Args:
            indice: posição da entrada em `entradas`.

        Returns:
            None. Se a página falhar ao ser criada, a área de conteúdo mostra a mensagem de
            erro (e a criação é tentada de novo na próxima seleção).
        """
        self.botoes[indice].setChecked(True)
        pagina = self._paginas.get(indice)
        if pagina is None:
            try:
                pagina = self._entradas[indice][1]()
            except Exception as e:  # noqa: BLE001 - qualquer falha do módulo vira aviso na tela
                aviso = QLabel(f'Não foi possível abrir "{self._entradas[indice][0]}":\n{e}')
                aviso.setObjectName("erroMenu")
                aviso.setWordWrap(True)
                aviso.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                self._trocar(aviso, descartavel=True)
                return
            self._paginas[indice] = pagina
            self.pilha.addWidget(pagina)
        self._trocar(pagina)

    def _trocar(self, pagina: QWidget, descartavel: bool = False) -> None:
        """Exibe `pagina` na área de conteúdo, removendo um aviso de erro anterior.

        Args:
            pagina: widget a exibir.
            descartavel: True para avisos de erro, que não são guardados.

        Returns:
            None.
        """
        atual = self.pilha.currentWidget()
        if descartavel:
            self.pilha.addWidget(pagina)
        self.pilha.setCurrentWidget(pagina)
        if atual is not None and atual is not pagina and atual.objectName() == "erroMenu":
            self.pilha.removeWidget(atual)
            atual.deleteLater()


def main() -> None:
    """Abre o menu numa janela própria (sem login).

    Returns:
        None. Bloqueia até a janela ser fechada.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    janela = QMainWindow()
    janela.setWindowTitle("Monitor KPI")
    menu = PaginaMenu()
    menu.sair.connect(janela.close)  # sem login por aqui, "Sair" só fecha a janela
    janela.setCentralWidget(menu)
    janela.resize(1200, 800)
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
