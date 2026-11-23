"""Facade de autorização: permissões por cargo e por usuário, e administração de usuários.

Permissão efetiva = permissões do cargo (`cargo_permissao`) + concedidas ao usuário
- negadas ao usuário (`usuario_permissao`, coluna `concedida`). A negação vence a
concessão do cargo.

Uso:
    with DIC.db() as db:
        perms = FacedeAutorizacao(db).permissoes(user_id=1, cargo="comprador")
"""
from __future__ import annotations

from typing import Any

from ..dbAdapterInterface import dbAdapterInterface
from .interfaces.facedeAutorizacaoInterface import facedeAutorizacaoInterface

# Permissões que o sistema conhece (as rotas as exigem; o banco só as atribui).
PEDIDOS_LER = "pedidos:ler"
PEDIDOS_CRIAR = "pedidos:criar"
PEDIDOS_ALTERAR = "pedidos:alterar"
PEDIDOS_REMOVER = "pedidos:remover"
PEDIDOS_TODOS = "pedidos:todos"  # enxerga/altera pedidos de qualquer usuário
METRICAS_LER = "metricas:ler"
USUARIOS_GERENCIAR = "usuarios:gerenciar"

PERMISSOES = frozenset({
    PEDIDOS_LER, PEDIDOS_CRIAR, PEDIDOS_ALTERAR, PEDIDOS_REMOVER, PEDIDOS_TODOS,
    METRICAS_LER, USUARIOS_GERENCIAR,
})


def _valida(permissao: str) -> None:
    """Garante que a permissão é conhecida.

    Args:
        permissao: nome a validar.

    Raises:
        ValueError: se não estiver em `PERMISSOES`.
    """
    if permissao not in PERMISSOES:
        raise ValueError(f"permissão desconhecida: {permissao}")


class FacedeAutorizacao(facedeAutorizacaoInterface):
    """Implementação SQL do facade de autorização.

    Attributes:
        db: adapter de banco usado para as consultas.
    """

    def __init__(self, db: dbAdapterInterface) -> None:
        """Inicializa o facade com o adapter de banco.

        Args:
            db: adapter que satisfaz `dbAdapterInterface`.
        """
        self.db = db

    def permissoes(self, user_id: int, cargo: str) -> frozenset[str]:
        """Permissões efetivas do usuário (cargo + concessões - negações).

        Args:
            user_id: id do usuário.
            cargo: cargo do usuário.

        Returns:
            frozenset[str]: nomes das permissões efetivas.
        """
        efetivas = {r["permissao"] for r in self.db.fetch_all(
            "SELECT permissao FROM cargo_permissao WHERE cargo = ?", (cargo,))}
        for r in self.db.fetch_all(
                "SELECT permissao, concedida FROM usuario_permissao WHERE user_id = ?", (user_id,)):
            if r["concedida"] == 1:
                efetivas.add(r["permissao"])
            else:
                efetivas.discard(r["permissao"])
        return frozenset(efetivas)

    def obter_usuario(self, user_id: int) -> dict[str, Any] | None:
        """Dados públicos do usuário (nunca a senha).

        Args:
            user_id: id do usuário.

        Returns:
            dict[str, Any] | None: id, nome, cargo e ativo; None se não existir.
        """
        return self.db.fetch_one(
            "SELECT id, nome, cargo, ativo FROM usuario WHERE id = ?", (user_id,))

    def listar_usuarios(self, apenas_pendentes: bool = False) -> list[dict[str, Any]]:
        """Lista usuários por id (sem a senha).

        Args:
            apenas_pendentes: se True, só os inativos (aguardando validação).

        Returns:
            list[dict[str, Any]]: usuários encontrados.
        """
        where = "WHERE ativo = 0" if apenas_pendentes else ""
        return self.db.fetch_all(f"SELECT id, nome, cargo, ativo FROM usuario {where} ORDER BY id")

    def atualizar_usuario(self, user_id: int, ativo: bool | None = None,
                          cargo: str | None = None) -> bool:
        """Ativa/desativa o usuário e/ou troca o cargo.

        Args:
            user_id: id do usuário.
            ativo: novo estado, ou None para manter.
            cargo: novo cargo, ou None para manter.

        Returns:
            bool: True se o usuário existe.

        Raises:
            ValueError: se nada for informado ou o cargo for vazio.
        """
        sets, params = [], []
        if ativo is not None:
            sets.append("ativo = ?")
            params.append(1 if ativo else 0)
        if cargo is not None:
            if not cargo.strip():
                raise ValueError("cargo não pode ser vazio")
            sets.append("cargo = ?")
            params.append(cargo.strip())
        if not sets:
            raise ValueError("informe ativo e/ou cargo")
        cur = self.db.execute(f"UPDATE usuario SET {', '.join(sets)} WHERE id = ?",
                              [*params, user_id])
        return cur.rowcount > 0

    def definir_permissao_usuario(self, user_id: int, permissao: str, concedida: bool) -> bool:
        """Cria/atualiza a exceção do usuário para a permissão.

        Args:
            user_id: id do usuário.
            permissao: nome da permissão (deve ser conhecida).
            concedida: True concede; False nega.

        Returns:
            bool: True se o usuário existe.

        Raises:
            ValueError: se a permissão for desconhecida.
        """
        _valida(permissao)
        if self.obter_usuario(user_id) is None:
            return False
        self.db.execute(
            "INSERT INTO usuario_permissao (user_id, permissao, concedida) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, permissao) DO UPDATE SET concedida = excluded.concedida",
            (user_id, permissao, 1 if concedida else 0))
        return True

    def remover_permissao_usuario(self, user_id: int, permissao: str) -> bool:
        """Remove a exceção do usuário para a permissão.

        Args:
            user_id: id do usuário.
            permissao: nome da permissão.

        Returns:
            bool: True se havia exceção e foi removida.

        Raises:
            ValueError: se a permissão for desconhecida.
        """
        _valida(permissao)
        cur = self.db.execute(
            "DELETE FROM usuario_permissao WHERE user_id = ? AND permissao = ?",
            (user_id, permissao))
        return cur.rowcount > 0
