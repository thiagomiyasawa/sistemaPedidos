"""Interface (contrato) do facade de autorização.

Autorização por tabela e ação: o cargo (`cargo_permissao`) define o padrão e a linha
do usuário (`usuario_permissao`), se existir para a tabela, a substitui. Inclui a
administração de usuários (ativar, mudar cargo).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

ACOES = ("criar", "atualizar", "deletar", "ler")


@dataclass(frozen=True)
class Permissao:
    """Autorização sobre uma tabela.

    Attributes:
        criar: pode inserir registros.
        atualizar: pode alterar registros.
        deletar: pode remover registros.
        ler: pode consultar registros.
        todos: as ações valem para registros de qualquer dono (senão, só os próprios).
    """

    criar: bool = False
    atualizar: bool = False
    deletar: bool = False
    ler: bool = False
    todos: bool = False

    def permite(self, acao: str) -> bool:
        """Indica se a ação é permitida.

        Args:
            acao: uma de `ACOES`.

        Returns:
            bool: True se permitida.

        Raises:
            ValueError: se a ação for desconhecida.
        """
        if acao not in ACOES:
            raise ValueError(f"ação desconhecida: {acao}")
        return getattr(self, acao)


@runtime_checkable
class facedeAutorizacaoInterface(Protocol):
    """Consulta e administração de permissões e usuários."""

    def permissoes(self, user_id: int, cargo_id: int) -> dict[str, Permissao]:
        """Permissões efetivas por tabela: a linha do usuário substitui a do cargo.

        Args:
            user_id: id do usuário.
            cargo_id: id do cargo do usuário.

        Returns:
            dict[str, Permissao]: nome da tabela (minúsculo) -> permissão.
        """
        ...

    def obter_usuario(self, user_id: int) -> dict[str, Any] | None:
        """Dados públicos do usuário (id, nome, cargo, ativo; nunca a senha).

        Args:
            user_id: id do usuário.

        Returns:
            dict[str, Any] | None: o usuário, ou None se não existir.
        """
        ...

    def listar_usuarios(self, apenas_pendentes: bool = False) -> list[dict[str, Any]]:
        """Lista usuários (id, nome, cargo, ativo) por id.

        Args:
            apenas_pendentes: se True, só os ainda inativos (aguardando validação).

        Returns:
            list[dict[str, Any]]: usuários encontrados.
        """
        ...

    def atualizar_usuario(self, user_id: int, ativo: bool | None = None,
                          cargo: str | None = None) -> bool:
        """Ativa/desativa o usuário e/ou troca o cargo (pelo nome).

        Args:
            user_id: id do usuário.
            ativo: novo estado, ou None para manter.
            cargo: nome do novo cargo, ou None para manter.

        Returns:
            bool: True se o usuário existe (e foi atualizado).

        Raises:
            ValueError: se nada for informado ou o cargo não existir.
        """
        ...

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
        ...

    def remover_permissao_usuario(self, user_id: int, tabela: str) -> bool:
        """Remove a linha do usuário para a tabela (volta a valer a do cargo).

        Args:
            user_id: id do usuário.
            tabela: nome da tabela.

        Returns:
            bool: True se havia linha e foi removida.
        """
        ...
