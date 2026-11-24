"""Facade de produtos sobre a API HTTP.

`FacedeProdutoAPI` consulta `GET /produtos` pelo `adapterAPIInterface` (injetado; por padrão
`AdapterAPI`) e converte o JSON em entidades `Produto`.

Uso:
    with FacedeProdutoAPI() as produtos:
        catalogo = produtos.listar()
"""
from __future__ import annotations

from typing import Self

from client.adapters.adapterAPI import AdapterAPI
from client.adapters.interfaces.adapterAPIInterface import adapterAPIInterface
from client.paginas.sisPedidos.acessoServidor.interfaces.facedeProdutoAPIInterface import (
    facedeProdutoAPIInterface,
)
from client.paginas.sisPedidos.entidades.produto import Produto


class FacedeProdutoAPI(facedeProdutoAPIInterface):
    """Facade de produtos que consome o endpoint do catálogo da API HTTP.

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

    # --- produtos ----------------------------------------------------------
    def listar(self) -> list[Produto]:
        """Obtém o catálogo (`GET /produtos`).

        Returns:
            list[Produto]: produtos na ordem entregue pela API (categoria e código).

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        return [
            Produto(
                id=p["id"],
                codigo=p.get("codigo") or "",
                descricao=p.get("descricao") or "",
                categoria=p.get("categoria") or "",
            )
            for p in self.api.get("/produtos")
        ]
