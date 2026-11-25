"""Facade do carrinho sobre a API HTTP (`/carrinho`).

`FacedeCarrinhoAPI` fala com o servidor pelo `adapterAPIInterface` (injetado; por padrão
`AdapterAPI`) e converte o JSON em `ItemCarrinho`. O carrinho fica no banco, por usuário.

Uso:
    with FacedeCarrinhoAPI() as carrinho:
        carrinho.adicionar(7, 3, "m", date(2027, 3, 15))
        itens = carrinho.listar()
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any, Self

from client.adapters.adapterAPI import AdapterAPI
from client.adapters.interfaces.adapterAPIInterface import ApiError, adapterAPIInterface
from client.paginas.sisPedidos.acessoServidor.interfaces.facedeCarrinhoAPIInterface import (
    facedeCarrinhoAPIInterface,
)
from client.paginas.sisPedidos.entidades.itemCarrinho import ItemCarrinho
from client.paginas.sisPedidos.entidades.produto import Produto


def _para_itens(dados: list[dict[str, Any]]) -> list[ItemCarrinho]:
    """Converte o JSON do carrinho em entidades.

    Args:
        dados: lista de itens como devolvida pela API.

    Returns:
        list[ItemCarrinho]: itens na mesma ordem.
    """
    return [
        ItemCarrinho(
            produto=Produto(
                id=d["produto_id"],
                codigo=d.get("codigo") or "",
                descricao=d.get("descricao") or "",
                categoria=d.get("categoria") or "",
            ),
            quant=d["quantidade"],
            uni=d["unidade"],
            data_necessidade=date.fromisoformat(d["data_necessidade"]),
            id=d["id"],
        )
        for d in dados
    ]


class FacedeCarrinhoAPI(facedeCarrinhoAPIInterface):
    """Facade do carrinho que consome os endpoints `/carrinho` da API HTTP.

    Atributos:
        api: adapter de transporte usado nas requisições.
    """

    def __init__(self, api: adapterAPIInterface | None = None) -> None:
        """Inicializa o facade.

        Args:
            api: adapter HTTP a usar; se None cria um `AdapterAPI` padrão.
        """
        self.api: adapterAPIInterface = api or AdapterAPI()

    # --- ciclo de vida: fecha o adapter ------------------------------------
    def close(self) -> None:
        """Fecha o adapter e libera a conexão.

        Returns:
            None.
        """
        self.api.close()

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

    # --- carrinho ----------------------------------------------------------
    def listar(self) -> list[ItemCarrinho]:
        """Obtém os itens do carrinho (`GET /carrinho`).

        Returns:
            list[ItemCarrinho]: itens na ordem de inclusão.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        return _para_itens(self.api.get("/carrinho"))

    def adicionar(self, produto_id: int, quant: int, uni: str,
                  data_necessidade: date) -> list[ItemCarrinho]:
        """Soma `quant` ao produto na data e unidade (`POST /carrinho/itens`).

        O mesmo produto pode ter várias linhas, com datas ou unidades diferentes.

        Args:
            produto_id: produto a adicionar.
            quant: quantidade a somar (positiva).
            uni: unidade de medida da quantidade.
            data_necessidade: data em que o item é necessário.

        Returns:
            list[ItemCarrinho]: carrinho após a inclusão.

        Raises:
            ApiError: em falha de comunicação ou se a API recusar (ex.: produto inexistente).
        """
        return _para_itens(
            self.api.post("/carrinho/itens", json={
                "produto_id": produto_id, "quantidade": quant, "unidade": uni,
                "data_necessidade": data_necessidade.isoformat(),
            }))

    def remover(self, itens_ids: Iterable[int]) -> None:
        """Remove linhas do carrinho (`DELETE /carrinho/itens/{id}`), uma a uma.

        Linha que já não existe (404) é ignorada.

        Args:
            itens_ids: ids das linhas (`ItemCarrinho.id`) a remover.

        Returns:
            None.

        Raises:
            ApiError: em falha de comunicação ou erro da API diferente de 404.
        """
        for item_id in itens_ids:
            try:
                self.api.delete(f"/carrinho/itens/{item_id}")
            except ApiError as e:
                if e.status_code != 404:
                    raise

    def finalizar(self, obra: str, tarefa: str, local_entrega: str) -> int:
        """Fecha o carrinho (`POST /carrinho/finalizar`): o servidor monta o pedido e o esvazia.

        O cliente só envia os dados do pedido que o carrinho não tem; as linhas do carrinho já
        estão no servidor.

        Args:
            obra: obra do pedido.
            tarefa: tarefa da obra.
            local_entrega: local de entrega.

        Returns:
            int: número (id) do pedido criado.

        Raises:
            ApiError: em falha de comunicação ou se a API recusar (ex.: carrinho vazio, sem
                permissão de criar pedidos).
        """
        pedido = self.api.post("/carrinho/finalizar", json={
            "obra": obra, "tarefa": tarefa, "local_entrega": local_entrega})
        return pedido["id"]

    def limpar(self) -> None:
        """Esvazia o carrinho (`DELETE /carrinho`).

        Returns:
            None.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        self.api.delete("/carrinho")
