"""Valores disponíveis para os filtros.

GET /filtros          — obras, status e origens distintos (sem parâmetros).
GET /filtros/tarefas  — tarefas de uma obra; `obra` é obrigatória (tarefa só existe dentro de uma obra).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .validacoes import Obra


class ValoresFiltrosSaida(BaseModel):
    """Resposta de `GET /filtros` com os valores distintos disponíveis.

    Campos:
        obras: Obras distintas.
        status: Status distintos.
        origens: Origens distintas.
    """

    obras: list[str]
    status: list[str]
    origens: list[str]


class TarefasEntrada(BaseModel):
    """Parâmetros (query string) de `GET /filtros/tarefas`.

    Campos:
        obra: Obra cujas tarefas serão listadas (obrigatória).
    """

    model_config = ConfigDict(extra="forbid")  # parâmetros desconhecidos → 422

    obra: Obra  # obrigatória


TarefasSaida = list[str]
