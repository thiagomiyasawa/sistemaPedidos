"""Facade de acesso a pedidos.

Ponto único para as operações sobre `Pedido`/`ItemPedido`, escondendo o SQL e
as transações. Depende apenas de `dbAdapterInterface`.

Uso:
    with DIC.db() as db:
        facede = FacedePedido(db)
        pedido = facede.salvar(Pedido(num_itens=1, status_atual="novo", origem="RM",
                                      local_entrega="Obra A", obra="A", tarefa="T1"))
"""
from __future__ import annotations

from ..dbAdapterInterface import dbAdapterInterface
from ..entidades.pedidos import ItemPedido, Pedido
from .interfaces.facedePedidoInterface import facedePedidoInterface


class FacedePedido(facedePedidoInterface):
    """Implementação SQL do facade de pedidos (CRUD de `Pedido` e `ItemPedido`).

    Attributes:
        db: adapter de banco usado para as consultas e transações.
    """

    def __init__(self, db: dbAdapterInterface) -> None:
        """Inicializa o facade com o adapter de banco.

        Args:
            db: adapter que satisfaz `dbAdapterInterface`.
        """
        self.db = db

    def obter(self, pedido_id: int, com_itens: bool = True) -> Pedido | None:
        """Busca um pedido pelo ID.

        Args:
            pedido_id: identificador do pedido.
            com_itens: se True, carrega também os itens.

        Returns:
            Pedido | None: o pedido, ou None se não existir.
        """
        row = self.db.fetch_one("SELECT * FROM pedido WHERE id = ?", (pedido_id,))
        if row is None:
            return None
        pedido = Pedido.from_row(row)
        if com_itens:
            pedido.itens = self.itens_do_pedido(pedido_id)
        return pedido

    def listar(self, obra: str | None = None, status_atual: str | None = None,
               limit: int = 100, offset: int = 0) -> list[Pedido]:
        """Lista pedidos (sem itens) ordenados por ID, com filtros e paginação.

        Args:
            obra: filtra por obra, se informada.
            status_atual: filtra por status, se informado.
            limit: máximo de pedidos retornados.
            offset: quantidade de pedidos a pular.

        Returns:
            list[Pedido]: pedidos encontrados (lista vazia se nenhum).
        """
        filtros, params = [], []
        for col, val in (("obra", obra), ("status_atual", status_atual)):
            if val:
                filtros.append(f"{col} = ?")
                params.append(val)
        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        rows = self.db.fetch_all(
            f"SELECT * FROM pedido {where} ORDER BY id LIMIT ? OFFSET ?",
            [*params, limit, offset])
        return [Pedido.from_row(r) for r in rows]

    def itens_do_pedido(self, pedido_id: int) -> list[ItemPedido]:
        """Devolve os itens de um pedido.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            list[ItemPedido]: itens do pedido (vazia se não houver).
        """
        rows = self.db.fetch_all(
            "SELECT * FROM item_pedido WHERE id_pedido = ?", (pedido_id,))
        return [ItemPedido.from_row(r) for r in rows]

    def salvar(self, pedido: Pedido) -> Pedido:
        """Insere (id None) ou atualiza o pedido; itens novos (sem id_pedido) são inseridos.

        Tudo ocorre em uma única transação.

        Args:
            pedido: pedido a gravar; seu `id` (e o dos itens novos) é preenchido.

        Returns:
            Pedido: o pedido relido do banco, com itens.

        Raises:
            Exception: erros do banco (ex.: violação de integridade) após rollback.
        """
        with self.db.transaction():
            if pedido.id is None:
                pedido.id = self.db.insert("pedido", pedido.to_row())
            else:
                dados = pedido.to_row()
                dados.pop("id")
                sets = ", ".join(f"{c} = :{c}" for c in dados)
                self.db.execute(f"UPDATE pedido SET {sets} WHERE id = :_id",
                                {**dados, "_id": pedido.id})
            # `id` do item = número sequencial dentro do pedido (1, 2, 3...).
            ultimo = self.db.fetch_one(
                "SELECT COALESCE(MAX(id), 0) AS n FROM item_pedido WHERE id_pedido = ?",
                (pedido.id,))["n"]
            for item in pedido.itens:
                if item.id_pedido is None:
                    ultimo += 1
                    item.id = ultimo
                    item.id_pedido = pedido.id
                    self.db.insert("item_pedido", item.to_row())
        return self.obter(pedido.id)  # type: ignore[return-value]

    def remover(self, pedido_id: int) -> bool:
        """Remove o pedido e seus itens, em uma transação.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            bool: True se o pedido existia e foi removido.
        """
        with self.db.transaction():
            self.db.execute("DELETE FROM item_pedido WHERE id_pedido = ?", (pedido_id,))
            cur = self.db.execute("DELETE FROM pedido WHERE id = ?", (pedido_id,))
            return cur.rowcount > 0
