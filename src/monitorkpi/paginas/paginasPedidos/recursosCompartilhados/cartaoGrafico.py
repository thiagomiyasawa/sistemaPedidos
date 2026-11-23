"""`CartaoGrafico`: cartão base de todos os gráficos das páginas de pedidos."""
from __future__ import annotations

from abc import abstractmethod

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QHorizontalBarSeries,
    QValueAxis,
)
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QPainter, QPalette
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from bancoDadosSQL.entidades.pedidos import Pedido
from monitorkpi.paginas.paginasPedidos.recursosCompartilhados.dadosPedidos import DadosPedidos

CORES = ["#2E86AB", "#F6AE2D", "#3BB273", "#E15554", "#7768AE", "#F26419", "#33658A"]


class CartaoGrafico(QFrame):
    """Cartão com título, opções do gráfico e um gráfico.

    Não consulta a API: a página busca os pedidos (com o filtro geral) e os entrega por `definir_dados`.
    Subclasses implementam `construir_filtros` e `construir_grafico`.

    Attributes:
        titulo: Título exibido no topo do cartão (sobrescrito nas subclasses).
        precisa_top_itens: Se True, a página deve buscar também o top de itens.
        filtros: Widgets das opções próprias do gráfico, indexados pela chave.
        dados: Dados entregues pela página, ou None enquanto não houver.
        chart: `QChart` onde as séries são desenhadas.
        view: `QChartView` que exibe o `chart`.
        lbl_vazio: Rótulo exibido quando não há dados ou há erro.
        barra: Layout horizontal que contém as opções do gráfico.
    """

    titulo = "Gráfico"
    precisa_top_itens = False  # True se o gráfico usa o top de itens (consulta de métricas)

    def __init__(self) -> None:
        """Monta o cartão (título, barra de opções, gráfico e rótulo de vazio).

        Args:
            Nenhum.

        Returns:
            None. O widget fica pronto para receber dados por `definir_dados`.
        """
        super().__init__()
        self.setObjectName("cartao")
        self.setMinimumSize(460, 380)
        self.filtros: dict[str, QWidget] = {}  # opções próprias do gráfico (não filtram pedidos)
        self.dados: DadosPedidos | None = None  # entregues pela página (ela faz as requisições)

        self.chart = QChart()
        # O tema padrão do QChart tem texto escuro; com o tema escuro do sistema ele some no fundo.
        escuro = self.palette().color(QPalette.Base).lightness() < 128
        self.chart.setTheme(QChart.ChartThemeDark if escuro else QChart.ChartThemeLight)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        self.chart.setMargins(QMargins(0, 0, 0, 0))
        self.chart.setBackgroundVisible(False)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.view = QChartView(self.chart)
        self.view.setRenderHint(QPainter.Antialiasing)

        self.lbl_vazio = QLabel("Sem dados para os filtros selecionados")
        self.lbl_vazio.setAlignment(Qt.AlignCenter)
        self.lbl_vazio.setObjectName("vazio")

        titulo = QLabel(self.titulo)
        titulo.setObjectName("titulo")
        self.barra = QHBoxLayout()
        self.barra.setSpacing(8)

        lay = QVBoxLayout(self)
        lay.addWidget(titulo)
        lay.addLayout(self.barra)
        lay.addWidget(self.view, 1)
        lay.addWidget(self.lbl_vazio, 1)

        self.construir_filtros()
        self.barra.addStretch(1)

    # -- opções do gráfico
    def add_combo(self, chave: str, rotulo: str, itens: list[str]) -> QComboBox:
        """Adiciona à barra de opções um combo que redesenha o gráfico ao mudar.

        Args:
            chave: Identificador da opção (usado em `valor`).
            rotulo: Texto pequeno exibido acima do combo.
            itens: Textos das opções do combo.

        Returns:
            O `QComboBox` criado.
        """
        cb = QComboBox()
        cb.addItems(itens)
        cb.currentIndexChanged.connect(self.atualizar)
        self._add_filtro(chave, rotulo, cb)
        return cb

    def add_spin(self, chave: str, rotulo: str, minimo: int, maximo: int, valor: int) -> QSpinBox:
        """Adiciona à barra de opções um campo numérico que redesenha o gráfico ao mudar.

        Args:
            chave: Identificador da opção (usado em `valor`).
            rotulo: Texto pequeno exibido acima do campo.
            minimo: Menor valor permitido.
            maximo: Maior valor permitido.
            valor: Valor inicial.

        Returns:
            O `QSpinBox` criado.
        """
        sp = QSpinBox()
        sp.setRange(minimo, maximo)
        sp.setValue(valor)
        sp.valueChanged.connect(self.atualizar)
        self._add_filtro(chave, rotulo, sp)
        return sp

    def _add_filtro(self, chave: str, rotulo: str, w: QWidget) -> None:
        """Coloca o widget com seu rótulo na barra de opções e o registra em `filtros`.

        Args:
            chave: Identificador da opção.
            rotulo: Texto exibido acima do widget.
            w: Widget de entrada (combo, spin etc.).

        Returns:
            None.
        """
        box = QVBoxLayout()
        box.setSpacing(2)
        lbl = QLabel(rotulo)
        lbl.setObjectName("rotuloFiltro")
        box.addWidget(lbl)
        box.addWidget(w)
        self.barra.addLayout(box)
        self.filtros[chave] = w

    def valor(self, chave: str):
        """Lê o valor atual de uma opção do gráfico.

        Args:
            chave: Identificador da opção registrada em `filtros`.

        Returns:
            O texto atual (str) se for combo; o valor numérico (int) nos demais casos.

        Raises:
            KeyError: Se a chave não existir em `filtros`.
        """
        w = self.filtros[chave]
        if isinstance(w, QComboBox):
            return w.currentText()
        return w.value()

    # -- gráfico
    def limpar(self) -> None:
        """Remove todas as séries e eixos do gráfico.

        Args:
            Nenhum.

        Returns:
            None.
        """
        self.chart.removeAllSeries()
        for ax in self.chart.axes():
            self.chart.removeAxis(ax)

    def mostrar(self, tem_dados: bool) -> None:
        """Alterna entre o gráfico e a mensagem de "sem dados".

        Args:
            tem_dados: True mostra o gráfico; False mostra o rótulo de vazio.

        Returns:
            None.
        """
        self.view.setVisible(tem_dados)
        self.lbl_vazio.setVisible(not tem_dados)

    def eixos_categoria(self, serie, categorias: list[str], horizontal: bool = False) -> None:
        """Anexa eixo de categorias + eixo de valores inteiros à série.

        Adiciona a série ao gráfico e ajusta a escala do eixo de valores ao maior valor da série.

        Args:
            serie: Série de barras (`QBarSeries`, `QHorizontalBarSeries` ou empilhada).
            categorias: Rótulos do eixo de categorias.
            horizontal: Se True, categorias à esquerda e valores embaixo.

        Returns:
            None.
        """
        self.chart.addSeries(serie)
        cat = QBarCategoryAxis()
        cat.append(categorias)
        val = QValueAxis()
        val.setLabelFormat("%d")
        val.setTickType(QValueAxis.TicksDynamic)
        val.setTickInterval(1)
        val.setMin(0)
        pos_cat, pos_val = (Qt.AlignLeft, Qt.AlignBottom) if horizontal else (Qt.AlignBottom, Qt.AlignLeft)
        self.chart.addAxis(cat, pos_cat)
        self.chart.addAxis(val, pos_val)
        serie.attachAxis(cat)
        serie.attachAxis(val)
        maximo = max((s.at(i) for s in serie.barSets() for i in range(s.count())), default=1)
        val.setRange(0, max(1, maximo * 1.15))
        val.applyNiceNumbers()
        if maximo > 8:
            val.setTickType(QValueAxis.TicksFixed)
            val.setTickCount(6)

    def barras(self, rotulos: list[str], valores: list[float], horizontal: bool = False,
               cor: str = CORES[0]) -> None:
        """Desenha um gráfico de barras de uma única série ("Quantidade") com rótulos de valor.

        Args:
            rotulos: Nome de cada barra (categorias).
            valores: Valor de cada barra, na mesma ordem dos rótulos.
            horizontal: Se True, desenha barras horizontais.
            cor: Cor das barras (hexadecimal); padrão `CORES[0]`.

        Returns:
            None. Oculta a legenda do gráfico.
        """
        serie = QHorizontalBarSeries() if horizontal else QBarSeries()
        conj = QBarSet("Quantidade")
        conj.setColor(QColor(cor))
        conj.append(valores)
        serie.append(conj)
        serie.setLabelsVisible(True)
        self.eixos_categoria(serie, rotulos, horizontal)
        self.chart.legend().setVisible(False)

    # -- dados
    def pedidos(self) -> list[Pedido]:
        """Pedidos já filtrados entregues pela página.

        Args:
            Nenhum.

        Returns:
            Lista de `Pedido`.

        Raises:
            AttributeError: Se ainda não houver dados (`dados` é None).
        """
        return self.dados.pedidos

    def top_itens(self) -> list[tuple[str, int]]:
        """Top de itens entregue pela página.

        Args:
            Nenhum.

        Returns:
            Lista de tuplas (produto, quantidade total), do maior para o menor.

        Raises:
            AttributeError: Se ainda não houver dados (`dados` é None).
        """
        return self.dados.top_itens

    def atualizar(self) -> None:
        """Redesenha com os dados já recebidos da página (não consulta a API).

        Sem dados, apenas mostra a mensagem de vazio.

        Args:
            Nenhum.

        Returns:
            None.
        """
        self.limpar()
        if self.dados is None:
            self.mostrar(False)
            return
        self.lbl_vazio.setText("Sem dados para os filtros selecionados")
        self.construir_grafico()

    def definir_dados(self, dados: DadosPedidos) -> None:
        """Recebe os dados da página e redesenha o gráfico.

        Args:
            dados: Pedidos filtrados e, se pedido, o top de itens.

        Returns:
            None.
        """
        self.dados = dados
        self.atualizar()

    def mostrar_erro(self, erro: Exception) -> None:
        """Descarta os dados, limpa o gráfico e exibe a mensagem de falha da API.

        Args:
            erro: Exceção ocorrida na consulta (exibida na mensagem).

        Returns:
            None.
        """
        self.dados = None
        self.limpar()
        self.lbl_vazio.setText(f"Falha ao consultar a API: {erro}")
        self.mostrar(False)

    @abstractmethod
    def construir_filtros(self) -> None:
        """Cria as opções próprias do gráfico (via `add_combo`/`add_spin`); implementada nas subclasses.

        Args:
            Nenhum.

        Returns:
            None.
        """
        ...

    @abstractmethod
    def construir_grafico(self) -> None:
        """Desenha o gráfico a partir dos dados recebidos; implementada nas subclasses.

        Args:
            Nenhum.

        Returns:
            None. Deve chamar `mostrar` e adicionar séries/eixos ao `chart`.
        """
        ...
