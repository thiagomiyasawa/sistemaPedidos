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

    model_config = ConfigDict(extra="forbid")  # parâmetros desconhecidos → erro

    obra: Obra  # obrigatória

    def params(self) -> dict:
        """Parâmetros da query string.

        Returns:
            Dicionário com a chave `obra`.
        """
        return self.model_dump()


def para_dict(dados: dict) -> dict[str, list[str]]:
    """Valida o JSON de `GET /filtros` e o devolve como dicionário de listas.

    Args:
        dados: Dicionário JSON com as chaves `obras`, `status` e `origens`.

    Returns:
        Dicionário com as chaves `obras`, `status` e `origens`, cada uma uma lista de textos.

    Raises:
        pydantic.ValidationError: Se `dados` não corresponder ao formato esperado.
    """
    return ValoresFiltrosSaida.model_validate(dados).model_dump()


def para_lista(dados: list) -> list[str]:
    """Valida o JSON de `GET /filtros/tarefas` (lista de textos).

    Args:
        dados: Lista JSON de tarefas.

    Returns:
        Lista com cada elemento convertido para `str`.
    """
    return [str(v) for v in dados]
