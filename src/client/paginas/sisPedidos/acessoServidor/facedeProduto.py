"""Facade de produtos sobre a API HTTP.

`FacedeProdutoAPI` consulta `GET /produtos` pelo `adapterAPIInterface` (injetado; por padrão
`AdapterAPI`) e converte o JSON em entidades `Produto`.

Uso:
    with FacedeProdutoAPI() as produtos:
        pagina, total = produtos.listar_pagina(busca="cabo", limit=30, offset=0)
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
    def listar_pagina(self, busca: str | None = None, categoria: str | None = None,
                      limit: int = 30, offset: int = 0) -> tuple[list[Produto], int]:
        """Obtém uma página do catálogo (`GET /produtos`), já filtrada pelo servidor.

        Args:
            busca: texto procurado no código ou na descrição, se informado.
            categoria: filtra por categoria exata, se informada.
            limit: produtos por página.
            offset: quantidade de produtos a pular.

        Returns:
            tuple[list[Produto], int]: produtos da página (por categoria e código) e o total que
            casa com o filtro, somando todas as páginas.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        dados, total = self.api.get_pagina(
            "/produtos", busca=busca, categoria=categoria, limit=limit, offset=offset)
        return [
            Produto(
                id=p["id"],
                codigo=p.get("codigo") or "",
                descricao=p.get("descricao") or "",
                categoria=p.get("categoria") or "",
            )
            for p in dados
        ], total

    def categorias(self) -> list[str]:
        """Categorias distintas do catálogo (`GET /produtos/categorias`).

        Returns:
            list[str]: categorias em ordem alfabética.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        return self.api.get("/produtos/categorias")
