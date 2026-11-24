"""Tipos e regras de validação reutilizados pelos formulários da API.

Segurança: limites de tamanho/intervalo (evitam payloads gigantes e estouro de
inteiro no banco) e rejeição de caracteres de controle/invisíveis em textos
(NUL, quebras de linha, marcadores bidirecionais, etc.).
Integridade: faixas coerentes para ids, quantidades e datas.
"""
from __future__ import annotations

import unicodedata
from datetime import date, timedelta
from typing import Annotated

from fastapi import Path
from pydantic import AfterValidator, Field, StringConstraints

class ConflitoIntegridade(ValueError):
    """Entrada válida em si, mas que violaria a integridade dos dados já gravados."""


INT_MAX = 2**31 - 1          # cabe com folga no INTEGER do banco
MAX_ITENS_POR_PEDIDO = 500
QUANT_MAX = 1_000_000
DATA_MIN = date(2000, 1, 1)
DATA_MAX_ANOS_A_FRENTE = 10

# Categorias Unicode proibidas: controle (Cc), formatação/invisíveis (Cf), surrogates (Cs).
_PROIBIDAS = {"Cc", "Cf", "Cs"}


def _sem_caracteres_perigosos(valor: str) -> str:
    """Rejeita caracteres de controle/invisíveis e normaliza o texto.

    Args:
        valor: Texto a validar.

    Returns:
        O texto normalizado em Unicode NFC.

    Raises:
        ValueError: Se houver caractere das categorias Unicode Cc, Cf ou Cs.
    """
    for ch in valor:
        if unicodedata.category(ch) in _PROIBIDAS:
            raise ValueError(f"caractere não permitido (U+{ord(ch):04X})")
    return unicodedata.normalize("NFC", valor)


def texto(max_len: int, *, min_len: int = 1):
    """Texto aparado, com tamanho limitado e sem caracteres de controle.

    Args:
        max_len: Tamanho máximo permitido do texto.
        min_len: Tamanho mínimo permitido (padrão 1), após aparar espaços.

    Returns:
        Tipo `Annotated[str, ...]` para uso em campos pydantic.
    """
    return Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=min_len, max_length=max_len),
        AfterValidator(_sem_caracteres_perigosos),
    ]


def _data_plausivel(d: date) -> date:
    """Valida que a data está entre `DATA_MIN` e hoje + `DATA_MAX_ANOS_A_FRENTE` anos.

    Args:
        d: Data a validar.

    Returns:
        A mesma data, se válida.

    Raises:
        ValueError: Se a data estiver fora do intervalo permitido.
    """
    limite = date.today() + timedelta(days=365 * DATA_MAX_ANOS_A_FRENTE)
    if not DATA_MIN <= d <= limite:
        raise ValueError(f"data fora do intervalo permitido ({DATA_MIN} a {limite})")
    return d


# Campos de texto (limites por finalidade)
Status = texto(50)
Origem = texto(100)
Obra = texto(150)
Tarefa = texto(150)
LocalEntrega = texto(250)
Produto = texto(250)

# Numéricos
CodRM = Annotated[int, Field(ge=1, le=INT_MAX)]
Quantidade = Annotated[int, Field(gt=0, le=QUANT_MAX)]
DataNecessidade = Annotated[date, AfterValidator(_data_plausivel)]

# Parâmetro de caminho: id positivo e dentro da faixa do banco.
IdPedido = Annotated[int, Path(ge=1, le=INT_MAX)]