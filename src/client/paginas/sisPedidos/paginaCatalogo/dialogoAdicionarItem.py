"""Popup que pede os detalhes (quantidade, unidade e data de necessidade) do item do carrinho."""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from client.paginas.sisPedidos.entidades.produto import Produto
from client.paginas.sisPedidos.entidades.unidade import (
    TAM_MAX_UNIDADE,
    UNIDADE_PADRAO,
    UNIDADES,
)

QUANT_MAX = 1_000_000  # mesmo limite da API


class DialogoAdicionarItem(QDialog):
    """Mostra o produto e pede quantidade, unidade e data de necessidade (todas obrigatórias).

    A unidade tem lista de sugestões, mas aceita texto livre.

    Attributes:
        produto: Produto sendo adicionado.
        campo_quant: Campo da quantidade.
        campo_uni: Campo da unidade (combo editável).
        campo_data: Seletor da data de necessidade (obrigatória; sugere hoje + 7 dias).
        botoes: Botões "Adicionar ao carrinho" / "Cancelar".
    """

    def __init__(self, produto: Produto, parent: QWidget | None = None) -> None:
        """Monta o formulário; "Adicionar ao carrinho" só habilita com a unidade preenchida.

        Args:
            produto: produto a adicionar.
            parent: widget pai.
        """
        super().__init__(parent)
        self.produto = produto
        self.setWindowTitle("Adicionar ao carrinho")
        self.setMinimumWidth(400)

        titulo = QLabel(f"<b>{produto.codigo}</b> — {produto.descricao}".strip(" —"))
        titulo.setWordWrap(True)
        categoria = QLabel(produto.categoria)
        categoria.setEnabled(False)

        self.campo_quant = QSpinBox()
        self.campo_quant.setRange(1, QUANT_MAX)
        self.campo_quant.setValue(1)

        self.campo_uni = QComboBox()  # editável: as unidades são sugestões, vale qualquer texto
        self.campo_uni.setEditable(True)
        self.campo_uni.setInsertPolicy(QComboBox.NoInsert)
        self.campo_uni.lineEdit().setMaxLength(TAM_MAX_UNIDADE)
        self.campo_uni.addItems(UNIDADES)
        self.campo_uni.setCurrentText(UNIDADE_PADRAO)

        self.campo_data = QDateEdit(QDate.currentDate().addDays(7))
        self.campo_data.setCalendarPopup(True)
        self.campo_data.setDisplayFormat("dd/MM/yyyy")
        self.campo_data.setDateRange(QDate(2000, 1, 1), QDate.currentDate().addYears(10))  # como a API

        form = QFormLayout()
        form.addRow("Quantidade", self.campo_quant)
        form.addRow("Unidade", self.campo_uni)
        form.addRow("Necessário até", self.campo_data)

        self.botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botoes.button(QDialogButtonBox.Ok).setText("Adicionar ao carrinho")
        self.botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.botoes.accepted.connect(self.accept)
        self.botoes.rejected.connect(self.reject)
        self.campo_uni.editTextChanged.connect(self._validar)

        lay = QVBoxLayout(self)
        lay.addWidget(titulo)
        if produto.categoria:
            lay.addWidget(categoria)
        lay.addLayout(form)
        lay.addWidget(self.botoes)
        self._validar()
        self.campo_quant.setFocus()
        self.campo_quant.selectAll()

    def _validar(self) -> None:
        """Habilita "Adicionar ao carrinho" só quando a unidade tem texto (é obrigatória)."""
        self.botoes.button(QDialogButtonBox.Ok).setEnabled(bool(self.unidade()))

    def quantidade(self) -> int:
        """Quantidade escolhida.

        Returns:
            int: quantidade (>= 1).
        """
        return self.campo_quant.value()

    def unidade(self) -> str:
        """Unidade escolhida ou digitada, sem espaços nas pontas.

        Returns:
            str: texto da unidade (vazio se nada foi informado).
        """
        return self.campo_uni.currentText().strip()

    def data_necessidade(self) -> date:
        """Data de necessidade escolhida.

        Returns:
            date: a data selecionada.
        """
        return self.campo_data.date().toPython()
