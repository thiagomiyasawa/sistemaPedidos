"""Carrinho compartilhado entre as páginas (catálogo adiciona, carrinho exibe).

Os dados ficam no banco, por usuário, e são acessados pela API pelo facade do carrinho. Esta
classe mantém uma cópia local dos itens (para as telas lerem sem ir à API a cada redesenho) e
avisa as páginas por sinais. Objeto único por aplicação: `DIC.carrinho()`.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from PySide6.QtCore import QObject, Signal

from client.adapters.interfaces.adapterAPIInterface import ApiError
from client.facedes.interfaces.facedeCarrinhoAPIInterface import (
    facedeCarrinhoAPIInterface,
)
from client.entidades.itemCarrinho import ItemCarrinho
from client.entidades.produto import Produto


class Carrinho(QObject):
    """Itens do carrinho do usuário, guardados no banco via API.

    Cada alteração é gravada na API primeiro; só se der certo a cópia local é trocada pelo que o
    servidor devolveu. Se falhar, o estado local não muda e `falhou` é emitido com a mensagem.

    Signals:
        alterado(): emitido quando os itens locais mudam.
        falhou(str): emitido com a mensagem quando uma chamada à API falha.

    Attributes:
        itens: Linhas do carrinho, indexadas pelo id da linha (ordem de inclusão); o mesmo
            produto pode ter várias, com datas de necessidade ou unidades diferentes.
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
        self.itens = {i.id: i for i in itens}
        self.alterado.emit()

    def esquecer(self) -> None:
        """Descarta só a cópia local, sem tocar na API (usado no logout).

        Evita que o próximo usuário veja, por um instante, os itens do anterior; o carrinho
        dele é buscado por `recarregar()` quando a página é aberta.
        """
        self._definir([])

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

    def adicionar(self, produto: Produto, quant: int, uni: str, data_necessidade: date) -> bool:
        """Soma `quant` do produto, na data de necessidade e unidade, ao carrinho.

        Args:
            produto: Produto a adicionar.
            quant: Quantidade (positiva).
            uni: Unidade de medida da quantidade.
            data_necessidade: Data em que o item é necessário.

        Returns:
            bool: True se gravou; False se falhou (`falhou` é emitido).
        """
        try:
            self._definir(self._facede.adicionar(produto.id, quant, uni, data_necessidade))
        except ApiError as e:
            return self._falha(e)
        return True

    def remover(self, ids_itens: Iterable[int]) -> bool:
        """Remove as linhas informadas.

        Args:
            ids_itens: ids das linhas (`ItemCarrinho.id`) a remover.

        Returns:
            bool: True se gravou; False se falhou (`falhou` é emitido).
        """
        try:
            self._facede.remover(ids_itens)
            self._definir(self._facede.listar())
        except ApiError as e:
            return self._falha(e)
        return True

    def finalizar(self, obra: str, tarefa: str, local_entrega: str) -> int:
        """Fecha o carrinho: o servidor cria o pedido com as linhas dele e esvazia o carrinho.

        Diferente dos outros métodos, a falha sobe como `ApiError` (é uma ação pedida pelo
        usuário, que merece um aviso próprio); nesse caso o carrinho local não muda.

        Args:
            obra: obra do pedido.
            tarefa: tarefa da obra.
            local_entrega: local de entrega.

        Returns:
            int: número (id) do pedido criado.

        Raises:
            ApiError: se a API recusar (carrinho vazio, sem permissão...) ou falhar.
        """
        pedido_id = self._facede.finalizar(obra, tarefa, local_entrega)
        self._definir([])
        return pedido_id

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
