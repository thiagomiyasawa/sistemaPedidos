"""Diálogo que pede os dados do pedido ao finalizar o carrinho.

O carrinho tem produtos, quantidades, unidades e datas de necessidade; o pedido também precisa
de obra, tarefa e local de entrega, que o usuário informa aqui. É o servidor que monta o pedido
com as linhas do carrinho (status inicial e origem são definidos lá).
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class DadosPedido:
    """Dados que o usuário informa ao finalizar o carrinho.

    Attributes:
        obra: Obra do pedido.
        tarefa: Tarefa da obra.
        local_entrega: Local de entrega.
    """

    obra: str
    tarefa: str
    local_entrega: str


class DialogoNovoPedido(QDialog):
    """Formulário com obra, tarefa e local de entrega.

    Attributes:
        campo_obra: Campo da obra.
        campo_tarefa: Campo da tarefa.
        campo_local: Campo do local de entrega.
    """

    def __init__(self, n_itens: int, parent: QWidget | None = None) -> None:
        """Monta o formulário; o botão "Criar pedido" só habilita com os textos preenchidos.

        Args:
            n_itens: quantidade de itens distintos do pedido (só para o texto de cabeçalho).
            parent: widget pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Novo pedido")
        self.setMinimumWidth(420)

        self.campo_obra = QLineEdit()
        self.campo_obra.setMaxLength(150)
        self.campo_tarefa = QLineEdit()
        self.campo_tarefa.setMaxLength(150)
        self.campo_local = QLineEdit()
        self.campo_local.setMaxLength(250)

        form = QFormLayout()
        form.addRow("Obra", self.campo_obra)
        form.addRow("Tarefa", self.campo_tarefa)
        form.addRow("Local de entrega", self.campo_local)

        self.botoes = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botoes.button(QDialogButtonBox.Ok).setText("Criar pedido")
        self.botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.botoes.accepted.connect(self.accept)
        self.botoes.rejected.connect(self.reject)
        for campo in (self.campo_obra, self.campo_tarefa, self.campo_local):
            campo.textChanged.connect(self._validar)

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"{n_itens} item(ns) distintos serão enviados no pedido."))
        lay.addLayout(form)
        lay.addWidget(self.botoes)
        self._validar()

    def _validar(self) -> None:
        """Habilita "Criar pedido" só quando obra, tarefa e local têm texto."""
        ok = all(c.text().strip() for c in (self.campo_obra, self.campo_tarefa, self.campo_local))
        self.botoes.button(QDialogButtonBox.Ok).setEnabled(ok)

    def dados(self) -> DadosPedido:
        """Lê o que foi preenchido.

        Returns:
            DadosPedido: textos aparados.
        """
        return DadosPedido(
            obra=self.campo_obra.text().strip(),
            tarefa=self.campo_tarefa.text().strip(),
            local_entrega=self.campo_local.text().strip(),
        )
