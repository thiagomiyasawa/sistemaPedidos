"""Interface (contrato) do facade de autenticação.

Decide se uma credencial (chave de API) apresentada numa requisição é aceita e
emite chaves a partir de usuário e senha.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from .facedeAutorizacaoInterface import Permissao


@dataclass(frozen=True)
class Identidade:
    """Quem é o dono de uma chave de API válida.

    Attributes:
        user_id: id do usuário (`usuario.id`).
        cargo_id: id do cargo do usuário (`usuario.cargo_id`).
        cargo: nome do cargo.
        permissoes: permissões efetivas por tabela (preenchidas pelo gateway a cada
            requisição).
    """

    user_id: int
    cargo_id: int
    cargo: str
    permissoes: dict[str, Permissao] = field(default_factory=dict)


@runtime_checkable
class facedeAutenticacaoInterface(Protocol):
    """Operações de verificação de credenciais e emissão de chaves."""

    def autenticar(self, chave: str | None) -> Identidade | None:
        """Verifica a chave apresentada e identifica o dono.

        Uma chave vencida é removida do armazenamento ao ser apresentada.
        Chave de usuário inativo é recusada.

        Args:
            chave: chave recebida na requisição, ou None se ausente.

        Returns:
            Identidade | None: dono da chave se ela existe, não está vencida e o
            usuário está ativo; None caso contrário.
        """
        ...

    def login(self, nome: str, senha: str) -> tuple[str, datetime] | None:
        """Valida usuário e senha e devolve a chave de API do usuário.

        Se o usuário já tem uma chave não vencida, devolve essa mesma; senão emite
        uma nova.

        Args:
            nome: nome do usuário.
            senha: senha em texto puro informada no login.

        Returns:
            tuple[str, datetime] | None: (chave, vencimento em UTC); None se
            usuário inexistente, inativo ou senha incorreta.
        """
        ...

    def logout(self, chave: str) -> bool:
        """Revoga a chave (apaga do armazenamento).

        Args:
            chave: chave a revogar.

        Returns:
            bool: True se a chave existia e foi removida.
        """
        ...

    def registrar(self, nome: str, senha: str) -> int | None:
        """Cria um usuário novo, inativo até alguém validar o registro.

        Args:
            nome: nome do usuário (único, sem diferenciar maiúsculas).
            senha: senha em texto puro (guardada apenas como hash).

        Returns:
            int | None: id do usuário criado; None se o nome já estiver em uso.
        """
        ...
