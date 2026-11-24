"""Entidade `Produto` do catálogo, como o cliente a enxerga."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Produto:
    """Produto do catálogo.

    Attributes:
        id: Identificador do produto na API.
        codigo: Código do produto (texto vazio se o cadastro não tiver).
        descricao: Nome/descrição exibidos (texto vazio se o cadastro não tiver).
        categoria: Categoria para filtro (texto vazio se o cadastro não tiver).
    """

    id: int
    codigo: str
    descricao: str
    categoria: str
