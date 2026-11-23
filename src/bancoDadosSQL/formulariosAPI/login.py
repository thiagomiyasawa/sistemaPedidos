"""POST /login — troca usuário e senha por uma chave de API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginEntrada(BaseModel):
    """Corpo de `POST /login`.

    Campos:
        nome: Nome do usuário.
        senha: Senha do usuário.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(min_length=1, max_length=100)
    senha: str = Field(min_length=1, max_length=200)


class LoginSaida(BaseModel):
    """Resposta de `POST /login`.

    Campos:
        chave: Chave de API a enviar no cabeçalho `X-API-Key`.
        expira_em: Instante de vencimento da chave (UTC).
    """

    chave: str
    expira_em: datetime


class RegistroEntrada(BaseModel):
    """Corpo de `POST /registro`.

    Campos:
        nome: Nome do novo usuário (único, sem diferenciar maiúsculas).
        senha: Senha (mínimo de 8 caracteres).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nome: str = Field(min_length=1, max_length=100)
    senha: str = Field(min_length=8, max_length=200)


class RegistroSaida(BaseModel):
    """Resposta de `POST /registro`.

    Campos:
        nome: Nome do usuário.
        ativo: Sempre False: a conta só entra em uso após validação.
    """

    nome: str
    ativo: bool
