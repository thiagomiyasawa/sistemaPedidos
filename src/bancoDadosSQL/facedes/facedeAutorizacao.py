"""Facade de autorização por tabela e ação, e administração de usuários.

O cargo (`cargo_permissao`) define o padrão por tabela; se o usuário tem linha em
`usuario_permissao` para a tabela, ela SUBSTITUI a do cargo (pode negar o que o
cargo concede e conceder o que não concede).

Uso:
    with DIC.db() as db:
        perms = FacedeAutorizacao(db).permissoes(user_id=1, cargo_id=2)
        perms["pedido"].permite("criar")
"""
from __future__ import annotations

from typing import Any

from ..dbAdapterInterface import dbAdapterInterface
from .interfaces.facedeAutorizacaoInterface import Permissao, facedeAutorizacaoInterface

_COLUNAS = ("criar", "atualizar", "deletar", "ler", "todos")


def _permissao(row: dict[str, Any]) -> Permissao:
    """Converte uma linha de permissão (colunas 0/1) em `Permissao`.

    Args:
        row: linha com as colunas `criar`, `atualizar`, `deletar`, `ler` e `todos`.

    Returns:
        Permissao: a permissão correspondente.
    """
    return Permissao(**{c: row[c] == 1 for c in _COLUNAS})


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

    def permissoes(self, user_id: int, cargo_id: int) -> dict[str, Permissao]:
        """Permissões efetivas por tabela: a linha do usuário substitui a do cargo.

        Args:
            user_id: id do usuário.
            cargo_id: id do cargo do usuário.

        Returns:
            dict[str, Permissao]: nome da tabela (minúsculo) -> permissão.
        """
        # Uma consulta só: linhas do usuário + linhas do cargo das tabelas em que o
        # usuário NÃO tem linha (a do usuário substitui a do cargo).
        cols = ", ".join(_COLUNAS)
        rows = self.db.fetch_all(
            f"SELECT tabela, {cols} FROM usuario_permissao WHERE user_id = :u "
            f"UNION ALL "
            f"SELECT tabela, {cols} FROM cargo_permissao WHERE cargo_id = :c "
            f"AND tabela NOT IN (SELECT tabela FROM usuario_permissao WHERE user_id = :u)",
            {"u": user_id, "c": cargo_id})
        return {r["tabela"].lower(): _permissao(r) for r in rows}

    _USUARIO = ("SELECT u.id AS id, u.nome AS nome, u.cargo_id AS cargo_id, c.nome AS cargo, u.ativo AS ativo "
                "FROM usuario u JOIN cargos c ON c.id = u.cargo_id")

    def obter_usuario(self, user_id: int) -> dict[str, Any] | None:
        """Dados públicos do usuário (nunca a senha).

        Args:
            user_id: id do usuário.

        Returns:
            dict[str, Any] | None: id, nome, cargo e ativo; None se não existir.
        """
        return self.db.fetch_one(f"{self._USUARIO} WHERE u.id = ?", (user_id,))

    def listar_usuarios(self, apenas_pendentes: bool = False) -> list[dict[str, Any]]:
        """Lista usuários por id (sem a senha).

        Args:
            apenas_pendentes: se True, só os inativos (aguardando validação).

        Returns:
            list[dict[str, Any]]: usuários encontrados.
        """
        where = "WHERE u.ativo = 0" if apenas_pendentes else ""
        return self.db.fetch_all(f"{self._USUARIO} {where} ORDER BY u.id")

    def atualizar_usuario(self, user_id: int, ativo: bool | None = None,
                          cargo: str | None = None) -> bool:
        """Ativa/desativa o usuário e/ou troca o cargo (pelo nome).

        Args:
            user_id: id do usuário.
            ativo: novo estado, ou None para manter.
            cargo: nome do novo cargo, ou None para manter.

        Returns:
            bool: True se o usuário existe.

        Raises:
            ValueError: se nada for informado ou o cargo não existir.
        """
        sets, params = [], []
        if ativo is not None:
            sets.append("ativo = ?")
            params.append(1 if ativo else 0)
        if cargo is not None:
            linha = self.db.fetch_one("SELECT id FROM cargos WHERE nome = ?", (cargo.strip(),))
            if linha is None:
                raise ValueError(f"cargo desconhecido: {cargo}")
            sets.append("cargo_id = ?")
            params.append(linha["id"])
        if not sets:
            raise ValueError("informe ativo e/ou cargo")
        cur = self.db.execute(f"UPDATE usuario SET {', '.join(sets)} WHERE id = ?",
                              [*params, user_id])
        return cur.rowcount > 0

    def definir_permissao_usuario(self, user_id: int, tabela: str, permissao: Permissao) -> bool:
        """Cria/substitui a linha do usuário para a tabela.

        Args:
            user_id: id do usuário.
            tabela: nome de uma tabela cadastrada em `tabelas`.
            permissao: autorização que passa a valer no lugar da do cargo.

        Returns:
            bool: True se o usuário existe.

        Raises:
            ValueError: se a tabela não estiver cadastrada.
        """
        t = self.db.fetch_one("SELECT nome FROM tabelas WHERE nome = ?", (tabela,))
        if t is None:
            raise ValueError(f"tabela desconhecida: {tabela}")
        if self.obter_usuario(user_id) is None:
            return False
        valores = [1 if getattr(permissao, c) else 0 for c in _COLUNAS]
        self.db.execute(
            "INSERT INTO usuario_permissao (user_id, tabela, criar, atualizar, deletar, ler, todos) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(user_id, tabela) DO UPDATE SET "
            + ", ".join(f"{c} = excluded.{c}" for c in _COLUNAS),
            (user_id, t["nome"], *valores))
        return True

    def remover_permissao_usuario(self, user_id: int, tabela: str) -> bool:
        """Remove a linha do usuário para a tabela (volta a valer a do cargo).

        Args:
            user_id: id do usuário.
            tabela: nome da tabela.

        Returns:
            bool: True se havia linha e foi removida.
        """
        cur = self.db.execute(
            "DELETE FROM usuario_permissao WHERE user_id = ? AND tabela = ?", (user_id, tabela))
        return cur.rowcount > 0
