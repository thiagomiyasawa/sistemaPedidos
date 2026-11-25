"""Facade de pedidos para testes: liga direto ao banco SQLite, sem passar pela API.

Reaproveita o `FacedePedido` do módulo `bancoDadosSQL` (mesmo contrato `facedePedidoInterface`)
e acrescenta os extras que o `FacedePedidoAPI` oferece (`listar_todos`, `health`, `close`,
`with`), de modo que pode ser usado no lugar dele, por exemplo:

    DIC.facede_pedido.override(providers.Singleton(FacedePedidoTeste))
"""

from __future__ import annotations

from typing import Self

from bancoDadosSQL.dbAdapterInterface import dbAdapterInterface
from bancoDadosSQL.entidades.pedidos import Pedido
from bancoDadosSQL.facedes.facedePedido import FacedePedido
from bancoDadosSQL.SQLite.SQLiteAdapter import SQLiteAdapter
from client.paginas.monitorkpi.acessoServidor.interfaces.facedePedidoAPIInterface import (
    facedePedidoAPIInterface,
)


class FacedePedidoTeste(FacedePedido, facedePedidoAPIInterface):
    """Facade de pedidos para testes, ligado direto ao banco (sem API).

    Herda o CRUD de `FacedePedido` e acrescenta `health`, `listar_todos` e o
    ciclo de vida (`close`, `with`) exigidos por `facedePedidoAPIInterface`.
    O adapter de banco fica em `self.db`.
    """

    def __init__(self, db: dbAdapterInterface | None = None) -> None:
        """Inicializa o facade.

        Args:
            db: adapter de banco; se None cria um `SQLiteAdapter` padrão.
        """
        super().__init__(db or SQLiteAdapter())

    # --- ciclo de vida -----------------------------------------------------
    def close(self) -> None:
        """Fecha a conexão com o banco.

        Returns:
            None.
        """
        self.db.close()

    def __enter__(self) -> Self:
        """Entra no contexto `with`.

        Returns:
            O próprio facade.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o facade.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None (exceções não são suprimidas).
        """
        self.close()

    # --- extras (mesma assinatura do FacedePedidoAPI) ----------------------
    def health(self) -> dict:
        """Verifica se as tabelas do banco existem.

        Returns:
            Dicionário com `status` ("ok" ou "degradado") e `tabelas`
            (mapa nome da tabela -> existe).
        """
        tabelas = {t: self.db.table_exists(t) for t in ("pedido", "item_pedido")}
        return {
            "status": "ok" if all(tabelas.values()) else "degradado",
            "tabelas": tabelas,
        }

    def listar_meus_pagina(self, status_atual: str | None = None, limit: int = 30,
                           offset: int = 0) -> tuple[list[Pedido], int]:
        """Sem usuário autenticado neste facade de teste, considera todos os pedidos.

        Args:
            status_atual: filtra por status, ou None.
            limit: pedidos por página.
            offset: quantidade de pedidos a pular.

        Returns:
            tuple[list[Pedido], int]: pedidos da página (do mais novo) e o total do filtro.
        """
        return (self.listar(None, status_atual, limit, offset, None, "desc"),
                self.contar(None, status_atual, None))

    def status_dos_meus(self) -> list[str]:
        """Sem usuário autenticado neste facade de teste, status de todos os pedidos.

        Returns:
            list[str]: status existentes.
        """
        return self.status_distintos(None)

    def listar_todos(
        self,
        obra: str | None = None,
        status_atual: str | None = None,
        tamanho_pagina: int = 1000,
    ) -> list[Pedido]:
        """Todos os pedidos do filtro, percorrendo a paginação.

        Args:
            obra: filtra por obra, ou None.
            status_atual: filtra por status, ou None.
            tamanho_pagina: quantidade de pedidos lidos por consulta.

        Returns:
            Lista completa de `Pedido` que casam com o filtro.
        """
        todos: list[Pedido] = []
        while True:
            lote = self.listar(
                obra, status_atual, limit=tamanho_pagina, offset=len(todos)
            )
            todos.extend(lote)
            if len(lote) < tamanho_pagina:
                return todos
