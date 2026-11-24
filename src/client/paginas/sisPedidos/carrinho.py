"""Carrinho compartilhado entre as páginas (catálogo adiciona, carrinho exibe).

Os dados ficam no banco, por usuário, e são acessados pela API pelo facade do carrinho. Esta
classe mantém uma cópia local dos itens (para as telas lerem sem ir à API a cada redesenho) e
avisa as páginas por sinais. Objeto único por aplicação: `DIC.carrinho()`.
"""
from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QObject, Signal

from client.adapters.interfaces.adapterAPIInterface import ApiError
from client.paginas.sisPedidos.acessoServidor.interfaces.facedeCarrinhoAPIInterface import (
    facedeCarrinhoAPIInterface,
)
from client.paginas.sisPedidos.entidades.itemCarrinho import ItemCarrinho
from client.paginas.sisPedidos.entidades.produto import Produto


class Carrinho(QObject):
    """Itens do carrinho do usuário, guardados no banco via API.

    Cada alteração é gravada na API primeiro; só se der certo a cópia local é trocada pelo que o
    servidor devolveu. Se falhar, o estado local não muda e `falhou` é emitido com a mensagem.

    Signals:
        alterado(): emitido quando os itens locais mudam.
        falhou(str): emitido com a mensagem quando uma chamada à API falha.

    Attributes:
        itens: Itens do carrinho, indexados pelo id do produto (ordem de inclusão).
    """

    alterado = Signal()
    falhou = Signal(str)

    def __init__(self, facede: facedeCarrinhoAPIInterface) -> None:
        """Cria o carrinho vazio (use `recarregar()` para buscar o do usuário).

        Args:
            facede: facade que acessa o carrinho na API.
        """
        super().__init__()
        self._facede = facede
        self.itens: dict[int, ItemCarrinho] = {}

    def _definir(self, itens: list[ItemCarrinho]) -> None:
        """Troca a cópia local pelos itens do servidor e avisa as páginas.

        Args:
            itens: itens como devolvidos pela API.
        """
        self.itens = {i.produto.id: i for i in itens}
        self.alterado.emit()

    def _falha(self, e: ApiError) -> bool:
        """Emite `falhou` com a mensagem do erro.

        Args:
            e: erro da API.

        Returns:
            bool: sempre False (para `return self._falha(e)`).
        """
        self.falhou.emit(str(e.detalhe or e))
        return False

    def recarregar(self) -> bool:
        """Busca o carrinho do usuário na API.

        Returns:
            bool: True se atualizou; False se falhou (`falhou` é emitido).
        """
        try:
            self._definir(self._facede.listar())
        except ApiError as e:
            return self._falha(e)
        return True

    def adicionar(self, produto: Produto, quant: int) -> bool:
        """Soma `quant` do produto ao carrinho.

        Args:
            produto: Produto a adicionar.
            quant: Quantidade (positiva).

        Returns:
            bool: True se gravou; False se falhou (`falhou` é emitido).
        """
        try:
            self._definir(self._facede.adicionar(produto.id, quant))
        except ApiError as e:
            return self._falha(e)
        return True

    def remover(self, ids_produto: Iterable[int]) -> bool:
        """Remove os produtos informados.

        Args:
            ids_produto: ids dos produtos a remover.

        Returns:
            bool: True se gravou; False se falhou (`falhou` é emitido).
        """
        try:
            self._facede.remover(ids_produto)
            self._definir(self._facede.listar())
        except ApiError as e:
            return self._falha(e)
        return True

    def limpar(self) -> bool:
        """Esvazia o carrinho.

        Returns:
            bool: True se gravou; False se falhou (`falhou` é emitido).
        """
        try:
            self._facede.limpar()
            self._definir([])
        except ApiError as e:
            return self._falha(e)
        return True
