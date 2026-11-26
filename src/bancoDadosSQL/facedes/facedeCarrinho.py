"""Facade do carrinho: itens que o usuário separou para o pedido (`carrinho_itens_cadastro`).

Uma linha é um produto numa data de necessidade e numa unidade (único por usuário + produto +
data + unidade): o mesmo produto pode ter várias linhas, com datas ou unidades diferentes. Depende apenas de `dbAdapterInterface`.

Uso:
    with DIC.db() as db:
        itens = FacedeCarrinho(db).listar(user_id=1)
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

from ..dbAdapterInterface import dbAdapterInterface
from ..entidades.pedidos import ItemPedido, Pedido
from .interfaces.facedeCarrinhoInterface import facedeCarrinhoInterface


STATUS_INICIAL = "Aberto"  # status do pedido criado a partir do carrinho
ORIGEM_PEDIDO = "Sistema de Pedidos"


class FacedeCarrinho(facedeCarrinhoInterface):
    """Implementação SQL do carrinho por usuário.

    Attributes:
        db: adapter de banco usado para executar as consultas.
    """

    def __init__(self, db: dbAdapterInterface) -> None:
        """Inicializa o facade com o adapter de banco.

        Args:
            db: adapter que satisfaz `dbAdapterInterface`.
        """
        self.db = db

    def listar(self, user_id: int) -> list[dict[str, Any]]:
        """Itens do carrinho, na ordem de inclusão, com os dados do produto.

        Args:
            user_id: dono do carrinho.

        Returns:
            list[dict[str, Any]]: itens com `id` (da linha), `produto_id`, `codigo`, `descricao`,
            `categoria`, `quantidade`, `unidade` e `data_necessidade` (texto ISO).
        """
        self.db.execute(
            "SELECT c.id, c.produto_id, p.codigo, p.descricao, p.categoria, c.quantidade, "
            "c.unidade, c.data_necessidade "
            "FROM carrinho_itens_cadastro c JOIN produtos p ON p.id = c.produto_id "
            "WHERE c.user_id = ? ORDER BY c.id",
            (user_id,),
        )
        linhas = self.db.fetch_all()
        return [dict(linha) for linha in linhas]

    def adicionar(self, user_id: int, produto_id: int, quantidade: int, unidade: str,
                  data_necessidade: date) -> bool:
        """Soma `quantidade` ao produto na data e unidade (cria a linha se não existir).

        Mesmo produto com data ou unidade diferente vira outra linha.

        Args:
            user_id: dono do carrinho.
            produto_id: produto a adicionar.
            quantidade: quantidade a somar (positiva).
            unidade: unidade de medida da quantidade.
            data_necessidade: data em que o item é necessário.

        Returns:
            bool: True se adicionou; False se o produto não existir.
        """
        data = data_necessidade.isoformat()
        afetadas = self.db.execute(
            "INSERT INTO carrinho_itens_cadastro (user_id, produto_id, quantidade, unidade, data_necessidade) "
            "SELECT ?, id, ?, ?, ? FROM produtos WHERE id = ? "
            "ON CONFLICT(user_id, produto_id, data_necessidade, unidade) "
            "DO UPDATE SET quantidade = quantidade + excluded.quantidade",
            (user_id, quantidade, unidade, data, produto_id),
        )
        return afetadas > 0

    def remover(self, user_id: int, itens_ids: Iterable[int]) -> int:
        """Remove linhas do carrinho (ids que não são do usuário ou não existem são ignorados).

        Args:
            user_id: dono do carrinho.
            itens_ids: ids das linhas a remover.

        Returns:
            int: quantas linhas foram removidas.
        """
        ids = list(itens_ids)
        if not ids:
            return 0
        marcas = ",".join("?" * len(ids))
        return self.db.execute(
            f"DELETE FROM carrinho_itens_cadastro WHERE user_id = ? AND id IN ({marcas})",
            (user_id, *ids),
        )

    def finalizar(self, user_id: int, obra: str, tarefa: str, local_entrega: str) -> int:
        """Cria o pedido do usuário com as linhas do carrinho e esvazia o carrinho.

        Tudo em uma única transação: se algo falhar, o pedido não é criado e o carrinho fica
        como estava.

        Args:
            user_id: dono do carrinho (e do pedido criado).
            obra: obra do pedido.
            tarefa: tarefa da obra.
            local_entrega: local de entrega.

        Returns:
            int: número (id) do pedido criado.

        Raises:
            ValueError: se o carrinho estiver vazio ou os dados violarem as regras do pedido.
        """
        with self.db.transaction():
            linhas = self.listar(user_id)
            if not linhas:
                raise ValueError("O carrinho está vazio")
            itens = [
                ItemPedido(
                    produto=" - ".join(t for t in (l["codigo"], l["descricao"]) if t),
                    quant=l["quantidade"],
                    uni=l["unidade"],
                    data_necessidade=l["data_necessidade"],
                )
                for l in linhas
            ]
            pedido = Pedido(
                num_itens=len(itens), status_atual=STATUS_INICIAL, origem=ORIGEM_PEDIDO,
                local_entrega=local_entrega, obra=obra, tarefa=tarefa, user_id=user_id, itens=itens)
            pedido.id = self.db.insert("pedido", pedido.to_row())
            for n, item in enumerate(itens, start=1):  # id do item = nº dentro do pedido
                item.id, item.id_pedido = n, pedido.id
                self.db.insert("item_pedido", item.to_row())
            self.db.execute("DELETE FROM carrinho_itens_cadastro WHERE user_id = ?", (user_id,))
        return pedido.id

    def limpar(self, user_id: int) -> None:
        """Esvazia o carrinho do usuário.

        Args:
            user_id: dono do carrinho.

        Returns:
            None.
        """
        self.db.execute("DELETE FROM carrinho_itens_cadastro WHERE user_id = ?", (user_id,))
