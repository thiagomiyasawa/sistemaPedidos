"""Esqueleto comum das páginas de KPIs de pedidos: cabeçalho, barra de filtros, grade de gráficos.

Cada página (geral, por obra) herda `PaginaKPIBase` e define só o que é seu: quais gráficos,
quais filtros e como montar o dicionário de filtros. A requisição à API é feita aqui, uma vez
por atualização, e o resultado é entregue a todos os gráficos.
"""

from __future__ import annotations

import sys
from abc import abstractmethod
from collections.abc import Callable

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from client.monitorkpi.acessoServidor.interfaces.adapterAPIInterface import ApiError
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.cartaoGrafico import (
    CartaoGrafico,
)
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.dadosPedidos import (
    carregar_dados,
)
from client.monitorkpi.paginas.paginasPedidos.recursosCompartilhados.estilo import (
    ESTILO,
)


class PaginaKPIBase(QWidget):
    """Página com filtro geral no topo e uma grade de `CartaoGrafico` abaixo.

    Attributes:
        TITULO: Título do cabeçalho da página.
        COLUNAS: Número de colunas da grade de cartões.
        cartoes: Cartões de gráfico criados por `criar_cartoes`.
        filtros: Combos do filtro geral, indexados pela chave.
        barra: Layout horizontal da barra de filtros.
    """

    TITULO = "KPIs de Pedidos"
    COLUNAS = 2

    def __init__(self) -> None:
        """Monta cabeçalho, barra de filtros e grade rolável de gráficos, e carrega os dados.

        Args:
            Nenhum.

        Returns:
            None. Ao final chama `aplicar_filtros` (faz a primeira consulta à API).
        """
        super().__init__()
        self.setStyleSheet(ESTILO)
        self.cartoes: list[CartaoGrafico] = self.criar_cartoes()
        self.filtros: dict[str, QComboBox] = {}

        cab = QHBoxLayout()
        t = QLabel(self.TITULO)
        t.setObjectName("cabecalho")
        btn = QPushButton("Atualizar tudo")
        btn.clicked.connect(self.aplicar_filtros)
        cab.addWidget(t)
        cab.addStretch(1)
        cab.addWidget(btn)

        self.barra = QHBoxLayout()
        self.barra.setSpacing(8)
        self.construir_filtros()
        self.barra.addStretch(1)

        grade = QGridLayout()
        grade.setSpacing(14)
        for i, c in enumerate(self.cartoes):
            grade.addWidget(c, i // self.COLUNAS, i % self.COLUNAS)
        conteudo = QWidget()
        conteudo.setLayout(grade)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.NoFrame)
        rolagem.setWidget(conteudo)

        lay = QVBoxLayout(self)
        lay.addLayout(cab)
        lay.addLayout(self.barra)
        lay.addWidget(rolagem, 1)

        self.aplicar_filtros()

    # -- para as subclasses
    @abstractmethod
    def criar_cartoes(self) -> list[CartaoGrafico]:
        """Cria os cartões de gráfico da página; implementada nas subclasses.

        Args:
            Nenhum.

        Returns:
            Lista de instâncias de `CartaoGrafico`, na ordem de exibição.
        """
        ...

    @abstractmethod
    def construir_filtros(self) -> None:
        """Monta a barra de filtros com `add_combo` / `add_controle`.

        Args:
            Nenhum.

        Returns:
            None.
        """

    @abstractmethod
    def filtros_atuais(self) -> dict:
        """Filtros no formato de `filtrar_pedidos`.

        Args:
            Nenhum.

        Returns:
            Dicionário com os filtros escolhidos (obra, status, origem, tarefa, dias ou de/ate).
        """

    # -- barra de filtros
    def add_controle(self, rotulo: str, w: QWidget) -> QWidget:
        """Põe um rótulo pequeno sobre o controle; devolve o contêiner (para mostrar/ocultar).

        Args:
            rotulo: Texto exibido acima do controle.
            w: Widget de entrada a ser colocado na barra de filtros.

        Returns:
            O `QWidget` contêiner (rótulo + controle) adicionado à barra.
        """
        caixa = QWidget()
        box = QVBoxLayout(caixa)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        lbl = QLabel(rotulo)
        lbl.setObjectName("rotuloFiltro")
        box.addWidget(lbl)
        box.addWidget(w)
        self.barra.addWidget(caixa)
        return caixa

    def add_combo(
        self,
        chave: str,
        rotulo: str,
        itens: list[str],
        padrao: str | None = None,
        ao_mudar: Callable[[], None] | None = None,
    ) -> QComboBox:
        """Adiciona um combo de filtro à barra e o registra em `filtros`.

        Args:
            chave: Identificador do filtro em `filtros`.
            rotulo: Texto exibido acima do combo.
            itens: Opções do combo.
            padrao: Texto inicialmente selecionado (opcional).
            ao_mudar: Função chamada quando a seleção muda; por padrão `aplicar_filtros`.

        Returns:
            O `QComboBox` criado.
        """
        cb = QComboBox()
        cb.addItems(itens)
        if padrao is not None:
            cb.setCurrentText(padrao)
        cb.currentIndexChanged.connect(ao_mudar or self.aplicar_filtros)
        self.add_controle(rotulo, cb)
        self.filtros[chave] = cb
        return cb

    # -- dados
    def aplicar_filtros(self) -> None:
        """Faz as requisições (uma vez) e entrega os dados a todos os gráficos.

        Em caso de `ApiError`, mostra a mensagem de erro em cada cartão (a exceção não se propaga).

        Args:
            Nenhum. Usa `filtros_atuais()`.

        Returns:
            None.
        """
        try:
            dados = carregar_dados(
                self.filtros_atuais(),
                com_top_itens=any(c.precisa_top_itens for c in self.cartoes),
            )
        except ApiError as e:
            for c in self.cartoes:
                c.mostrar_erro(e)
            return
        for c in self.cartoes:
            c.definir_dados(dados)


class JanelaPrincipal(QMainWindow):
    """Janela principal que hospeda uma página de KPIs como widget central."""

    def __init__(self, pagina: QWidget, titulo: str) -> None:
        """Configura título, widget central e tamanho inicial (1100x800).

        Args:
            pagina: Widget da página exibido no centro da janela.
            titulo: Título da janela.

        Returns:
            None.
        """
        super().__init__()
        self.setWindowTitle(titulo)
        self.setCentralWidget(pagina)
        self.resize(1100, 800)


def executar(classe_pagina: type[PaginaKPIBase], titulo: str) -> None:
    """Abre a página numa janela própria (usado ao rodar o arquivo da página diretamente).

    Args:
        classe_pagina: Classe (subclasse de `PaginaKPIBase`) a instanciar.
        titulo: Título da janela.

    Returns:
        None. Roda o loop de eventos e encerra o processo com `sys.exit` ao fechar a janela.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    janela = JanelaPrincipal(classe_pagina(), titulo)
    janela.show()
    sys.exit(app.exec())
