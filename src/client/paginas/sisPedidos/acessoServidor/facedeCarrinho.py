"""Facade do carrinho sobre a API HTTP (`/carrinho`).

`FacedeCarrinhoAPI` fala com o servidor pelo `adapterAPIInterface` (injetado; por padrão
`AdapterAPI`) e converte o JSON em `ItemCarrinho`. O carrinho fica no banco, por usuário.

Uso:
    with FacedeCarrinhoAPI() as carrinho:
        carrinho.adicionar(produto_id=7, quant=3)
        itens = carrinho.listar()
"""
from __future__ import annotations

from collections.abc import Iterable
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

    def adicionar(self, produto_id: int, quant: int) -> list[ItemCarrinho]:
        """Soma `quant` ao produto no carrinho (`POST /carrinho/itens`).

        Args:
            produto_id: produto a adicionar.
            quant: quantidade a somar (positiva).

        Returns:
            list[ItemCarrinho]: carrinho após a inclusão.

        Raises:
            ApiError: em falha de comunicação ou se a API recusar (ex.: produto inexistente).
        """
        return _para_itens(
            self.api.post("/carrinho/itens", json={"produto_id": produto_id, "quantidade": quant}))

    def remover(self, produtos_ids: Iterable[int]) -> None:
        """Remove produtos do carrinho (`DELETE /carrinho/itens/{id}`), um a um.

        Produto que já não está no carrinho (404) é ignorado.

        Args:
            produtos_ids: produtos a remover.

        Returns:
            None.

        Raises:
            ApiError: em falha de comunicação ou erro da API diferente de 404.
        """
        for produto_id in produtos_ids:
            try:
                self.api.delete(f"/carrinho/itens/{produto_id}")
            except ApiError as e:
                if e.status_code != 404:
                    raise

    def limpar(self) -> None:
        """Esvazia o carrinho (`DELETE /carrinho`).

        Returns:
            None.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        self.api.delete("/carrinho")
