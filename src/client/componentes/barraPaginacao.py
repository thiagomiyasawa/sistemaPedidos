"""Barra de paginação reutilizável (PySide6) para tabelas com muitos itens.

A barra só controla qual "fatia" da lista deve ser mostrada; quem a usa continua dono dos dados.
Há dois modos de uso. Paginação local (lista já carregada):

    self.paginacao = BarraPaginacao()
    self.paginacao.mudou.connect(self.desenhar)       # o usuário trocou de página
    ...
    self.paginacao.definir_total(len(itens))          # a cada nova lista
    for item in self.paginacao.fatia(itens): ...      # só os itens da página atual

Paginação no servidor: `definir_total` recebe o total devolvido pela API, `inicio` e `tamanho`
viram o `offset` e o `limit` da consulta, e `mudou` dispara a nova consulta (sem usar `fatia`).

Com no máximo `tamanho` itens a barra fica oculta.
"""
from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from typing import TypeVar

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

T = TypeVar("T")

TAMANHO_PAGINA = 30


class BarraPaginacao(QWidget):
    """Botões « ‹ › » e o texto "Página X de Y · a–b de N".

    Signals:
        mudou(): emitido quando o usuário muda de página (não ao chamar `definir_total`).

    Attributes:
        tamanho: Itens por página.
        pagina: Página atual, a partir de 0.
        total: Quantidade total de itens.
    """

    mudou = Signal()

    def __init__(self, tamanho: int = TAMANHO_PAGINA, parent: QWidget | None = None) -> None:
        """Cria a barra (oculta, pois começa sem itens).

        Args:
            tamanho: itens por página (positivo).
            parent: widget pai.
        """
        super().__init__(parent)
        if tamanho < 1:
            raise ValueError("tamanho da página deve ser >= 1")
        self.tamanho = tamanho
        self.pagina = 0
        self.total = 0

        def botao(texto: str, dica: str) -> QPushButton:
            b = QPushButton(texto)
            b.setToolTip(dica)
            b.setFixedWidth(34)
            b.setCursor(Qt.PointingHandCursor)
            return b

        self.primeira = botao("«", "Primeira página")
        self.anterior = botao("‹", "Página anterior")
        self.proxima = botao("›", "Próxima página")
        self.ultima = botao("»", "Última página")
        self.texto = QLabel()
        self.texto.setObjectName("vazio")
        self.primeira.clicked.connect(lambda: self.ir_para(0))
        self.anterior.clicked.connect(lambda: self.ir_para(self.pagina - 1))
        self.proxima.clicked.connect(lambda: self.ir_para(self.pagina + 1))
        self.ultima.clicked.connect(lambda: self.ir_para(self.paginas - 1))

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch(1)
        for w in (self.primeira, self.anterior, self.texto, self.proxima, self.ultima):
            lay.addWidget(w)
        self._atualizar()

    @property
    def paginas(self) -> int:
        """Quantidade de páginas (no mínimo 1).

        Returns:
            int: `ceil(total / tamanho)`, ou 1 se não houver itens.
        """
        return max(1, ceil(self.total / self.tamanho))

    @property
    def inicio(self) -> int:
        """Índice do primeiro item da página atual.

        Returns:
            int: posição inicial (a partir de 0).
        """
        return self.pagina * self.tamanho

    def definir_total(self, total: int, resetar: bool = False) -> None:
        """Informa a quantidade de itens da lista; não emite `mudou`.

        Args:
            total: quantidade total de itens.
            resetar: se True volta à primeira página (ex.: filtro ou pedido mudou); senão mantém
                a página atual, ajustada se a lista encolheu.
        """
        self.total = max(0, total)
        self.pagina = 0 if resetar else min(self.pagina, self.paginas - 1)
        self._atualizar()

    def voltar_ao_inicio(self) -> None:
        """Volta à primeira página sem emitir `mudou` (o chamador já vai consultar de novo)."""
        self.pagina = 0
        self._atualizar()

    def fatia(self, itens: Sequence[T]) -> Sequence[T]:
        """Itens da página atual.

        Args:
            itens: lista completa (a mesma cujo tamanho foi passado a `definir_total`).

        Returns:
            Sequence[T]: no máximo `tamanho` itens, a partir de `inicio`.
        """
        return itens[self.inicio:self.inicio + self.tamanho]

    def ir_para(self, pagina: int) -> None:
        """Vai para uma página (limitada ao intervalo válido) e emite `mudou` se ela mudou.

        Args:
            pagina: página desejada, a partir de 0.
        """
        pagina = max(0, min(pagina, self.paginas - 1))
        if pagina == self.pagina:
            return
        self.pagina = pagina
        self._atualizar()
        self.mudou.emit()

    def _atualizar(self) -> None:
        """Atualiza texto, botões e visibilidade (oculta se tudo cabe numa página)."""
        fim = min(self.inicio + self.tamanho, self.total)
        self.texto.setText(
            f"Página {self.pagina + 1} de {self.paginas} · {self.inicio + 1 if self.total else 0}–{fim} de {self.total}")
        self.primeira.setEnabled(self.pagina > 0)
        self.anterior.setEnabled(self.pagina > 0)
        self.proxima.setEnabled(self.pagina < self.paginas - 1)
        self.ultima.setEnabled(self.pagina < self.paginas - 1)
        self.setVisible(self.total > self.tamanho)
