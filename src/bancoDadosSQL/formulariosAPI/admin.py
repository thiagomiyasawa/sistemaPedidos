"""Rotas de administração de usuários e permissões (`/admin/usuarios`)."""
from __future__ import annotations

from typing import Annotated, Self

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .validacoes import INT_MAX

IdUsuario = Annotated[int, Path(ge=1, le=INT_MAX)]


class ListarUsuariosEntrada(BaseModel):
    """Filtro (query string) de `GET /admin/usuarios`.

    Campos:
        apenas_pendentes: Se True, só usuários inativos (aguardando validação).
    """

    model_config = ConfigDict(extra="forbid")

    apenas_pendentes: bool = False


class UsuarioSaida(BaseModel):
    """Dados públicos de um usuário.

    Campos:
        id: Identificador do usuário.
        nome: Nome do usuário.
        cargo: Cargo atual.
        ativo: Se o usuário pode logar.
    """

    id: int
    nome: str
    cargo: str
    ativo: bool


class AtualizarUsuarioEntrada(BaseModel):
    """Corpo de `PATCH /admin/usuarios/{id}`: informe `ativo` e/ou `cargo`.

    Campos:
        ativo: True valida/ativa o usuário; False desativa.
        cargo: Nome do novo cargo (define as permissões do usuário).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ativo: bool | None = None
    cargo: str | None = Field(default=None, min_length=1, max_length=50)

    @model_validator(mode="after")
    def _algum_campo(self) -> Self:
        """Exige ao menos um campo.

        Returns:
            A própria instância, se válida.

        Raises:
            ValueError: se `ativo` e `cargo` forem ambos omitidos.
        """
        if self.ativo is None and self.cargo is None:
            raise ValueError("informe ativo e/ou cargo")
        return self


class PermissaoUsuarioEntrada(BaseModel):
    """Corpo de `PUT /admin/usuarios/{id}/permissoes/{tabela}`.

    Substitui, para essa tabela, a autorização do cargo (o que não for informado
    fica False).

    Campos:
        criar: Pode inserir registros.
        atualizar: Pode alterar registros.
        deletar: Pode remover registros.
        ler: Pode consultar registros.
        todos: Vale para registros de qualquer dono, não só os próprios.
    """

    model_config = ConfigDict(extra="forbid")

    criar: bool = False
    atualizar: bool = False
    deletar: bool = False
    ler: bool = False
    todos: bool = False


class PermissaoSaida(PermissaoUsuarioEntrada):
    """Autorização efetiva sobre uma tabela (mesmos campos da entrada)."""


class PermissoesSaida(BaseModel):
    """Permissões efetivas de um usuário.

    Campos:
        usuario: Dados do usuário.
        permissoes: Mapa tabela -> autorização efetiva (cargo, ou usuário se houver).
    """

    usuario: UsuarioSaida
    permissoes: dict[str, PermissaoSaida]
