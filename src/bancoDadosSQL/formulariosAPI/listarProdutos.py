"""GET /produtos — sem corpo de entrada; devolve o catálogo de produtos."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


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
