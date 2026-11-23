"""Interface (contrato) do facade de autorização.

Permissões por cargo (`cargo_permissao`) com exceções por usuário
(`usuario_permissao`), mais a administração de usuários (ativar, mudar cargo).
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class facedeAutorizacaoInterface(Protocol):
    """Consulta e administração de permissões e usuários."""

    def permissoes(self, user_id: int, cargo: str) -> frozenset[str]:
        """Permissões efetivas: as do cargo, mais as concedidas e menos as negadas ao usuário.

        Args:
            user_id: id do usuário.
            cargo: cargo do usuário.

        Returns:
            frozenset[str]: nomes das permissões efetivas.
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
        """Ativa/desativa o usuário e/ou troca o cargo.

        Args:
            user_id: id do usuário.
            ativo: novo estado, ou None para manter.
            cargo: novo cargo, ou None para manter.

        Returns:
            bool: True se o usuário existe (e foi atualizado).

        Raises:
            ValueError: se nada for informado ou o cargo for vazio.
        """
        ...

    def definir_permissao_usuario(self, user_id: int, permissao: str, concedida: bool) -> bool:
        """Cria/atualiza a exceção do usuário: concede ou nega a permissão.

        Args:
            user_id: id do usuário.
            permissao: nome da permissão (deve ser conhecida).
            concedida: True concede (mesmo que o cargo não tenha); False nega.

        Returns:
            bool: True se o usuário existe.

        Raises:
            ValueError: se a permissão for desconhecida.
        """
        ...

    def remover_permissao_usuario(self, user_id: int, permissao: str) -> bool:
        """Remove a exceção do usuário (volta a valer o que o cargo define).

        Args:
            user_id: id do usuário.
            permissao: nome da permissão.

        Returns:
            bool: True se havia exceção e foi removida.

        Raises:
            ValueError: se a permissão for desconhecida.
        """
        ...
