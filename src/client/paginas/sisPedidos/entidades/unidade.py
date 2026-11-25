"""Unidades de medida sugeridas ao adicionar produtos ao carrinho (o campo aceita texto livre)."""
from __future__ import annotations

UNIDADES: tuple[str, ...] = (
    "un", "par", "cx", "pç", "rolo", "saco", "barra", "m", "m²", "m³", "kg", "l",
)
UNIDADE_PADRAO = "un"
TAM_MAX_UNIDADE = 20  # mesmo limite da API (`Unidade` em validacoes)
