"""Interface (contrato) do facade de pedidos usado pelo cliente.

Estende o contrato básico `facedePedidoInterface` com o que a interface gráfica
precisa além dele: `health`, `listar_todos` e o ciclo de vida (`close`, `with`).
Satisfazem este contrato `FacedePedidoAPI` (via HTTP) e `FacedePedidoTeste` (direto no
banco), podendo ser trocados no `DIC` sem alterar quem os usa.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from bancoDadosSQL.entidades.pedidos import Pedido
from bancoDadosSQL.facedes.interfaces.facedePedidoInterface import facedePedidoInterface

from client.adapters.interfaces.adapterAPIInterface import Json


@runtime_checkable
class facedePedidoAPIInterface(facedePedidoInterface, Protocol):
    """`facedePedidoInterface` + extras de consulta e ciclo de vida."""

    def health(self) -> Json:
        """Estado do servidor/banco e das tabelas.

        Returns:
            Dicionário JSON com o status geral e a situação das tabelas.
        """
        ...

    def listar_todos(
        self,
        obra: str | None = None,
        status_atual: str | None = None,
        tamanho_pagina: int = 1000,
    ) -> list[Pedido]:
        """Todos os pedidos que casam com o filtro (percorre a paginação).

        Args:
            obra: filtra por obra, ou None.
            status_atual: filtra por status, ou None.
            tamanho_pagina: quantidade de pedidos por requisição/página.

        Returns:
            Lista completa de `Pedido` que casam com o filtro.
        """
        ...

    def close(self) -> None:
        """Libera a conexão/recursos.

        Returns:
            None.
        """
        ...

    def __enter__(self) -> Self:
        """Entra no contexto `with`.

        Returns:
            O próprio facade.
        """
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o facade.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None.
        """
        ...
