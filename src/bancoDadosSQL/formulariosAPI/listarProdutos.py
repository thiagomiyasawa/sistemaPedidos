"""GET /produtos (catálogo paginado, com busca e categoria) e GET /produtos/categorias."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .validacoes import INT_MAX, texto

Busca = texto(100)
Categoria = texto(100)


class ListarProdutosEntrada(BaseModel):
    """Filtros e paginação (query string) de `GET /produtos`.

    Campos:
        busca: Texto procurado no código ou na descrição (opcional; sem diferenciar maiúsculas
            de minúsculas para letras ASCII).
        categoria: Filtra por categoria exata (opcional).
        limit: Máximo de produtos retornados (1 a 1000; padrão 100).
        offset: Quantidade de produtos a pular (0 até `INT_MAX`; padrão 0).

    O total de produtos que casam com o filtro vai no cabeçalho `X-Total-Count` da resposta.
    """

    model_config = ConfigDict(extra="forbid")  # parâmetros desconhecidos → 422

    busca: Busca | None = None
    categoria: Categoria | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0, le=INT_MAX)


class ProdutoSaida(BaseModel):
    """Produto do catálogo.

    Campos:
        id: Identificador do produto.
        codigo: Código do produto.
        descricao: Nome/descrição do produto.
        categoria: Categoria do produto.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str | None
    descricao: str | None
    categoria: str | None


ListarProdutosSaida = list[ProdutoSaida]
CategoriasSaida = list[str]
