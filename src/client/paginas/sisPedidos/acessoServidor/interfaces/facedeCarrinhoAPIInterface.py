"""Interface (contrato) do facade do carrinho usado pelo cliente.

O carrinho é guardado no banco, por usuário, e acessado pela API; o dono é o usuário da chave.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, Self, runtime_checkable

from client.paginas.sisPedidos.entidades.itemCarrinho import ItemCarrinho


@runtime_checkable
class facedeCarrinhoAPIInterface(Protocol):
    """Leitura e alteração do carrinho do usuário, mais o ciclo de vida."""

    def listar(self) -> list[ItemCarrinho]:
        """Itens do carrinho, na ordem de inclusão.

        Returns:
            list[ItemCarrinho]: itens do carrinho.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        ...

    def adicionar(self, produto_id: int, quant: int) -> list[ItemCarrinho]:
        """Soma `quant` ao produto no carrinho (cria o item se não existir).

        Args:
            produto_id: produto a adicionar.
            quant: quantidade a somar (positiva).

        Returns:
            list[ItemCarrinho]: carrinho após a inclusão.

        Raises:
            ApiError: em falha de comunicação ou se a API recusar (ex.: produto inexistente).
        """
        ...

    def remover(self, produtos_ids: Iterable[int]) -> None:
        """Remove produtos do carrinho (os que já não estão nele são ignorados).

        Args:
            produtos_ids: produtos a remover.

        Returns:
            None.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        ...

    def limpar(self) -> None:
        """Esvazia o carrinho.

        Returns:
            None.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        ...

    def close(self) -> None:
        """Libera a conexão/recursos.

        Returns:
            None.
        """
        ...

    def __enter__(self) -> Self:
        """Entra no contexto `with`."""
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o facade."""
        ...
