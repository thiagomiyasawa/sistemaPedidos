"""Interface (contrato) geral para adapters de banco de dados SQL.

Qualquer adapter (SQLite, PostgreSQL, ...) deve satisfazer `dbAdapterInterface`.
Como é um `Protocol`, não é necessário herdar dela: basta implementar os métodos.
"""
from __future__ import annotations

from collections.abc import Generator, Sequence
from contextlib import AbstractContextManager
from typing import Any, Protocol, Self, runtime_checkable

Params = Sequence[Any] | dict[str, Any]
Linha = dict[str, Any]


@runtime_checkable
class dbAdapterInterface(Protocol):
    """Contrato das operações básicas de acesso a um banco SQL.

    Uso:
        with MeuAdapter() as db:
            db.execute("INSERT INTO kpi (nome) VALUES (?)", ("vendas",))
            db.execute("SELECT * FROM kpi")
            linhas = db.fetch_all()
    """

    # --- conexão -----------------------------------------------------------
    def connect(self) -> Any:
        """Abre (ou reutiliza) a conexão e a devolve.

        Returns:
            Any: objeto de conexão nativo do driver.
        """
        ...

    def close(self) -> None:
        """Fecha a conexão, se aberta.

        Returns:
            None.
        """
        ...

    def __enter__(self) -> Self:
        """Entra no contexto `with`, abrindo a conexão.

        Returns:
            Self: o próprio adapter.
        """
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando a conexão.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None.
        """
        ...

    # --- transações --------------------------------------------------------
    def transaction(self) -> AbstractContextManager[Any]:
        """Commit ao sair normalmente, rollback em caso de exceção.

        Chamadas aninhadas participam da transação mais externa.

        Returns:
            AbstractContextManager[Any]: context manager que entrega a conexão.

        Raises:
            Exception: repropaga a exceção ocorrida no bloco, após o rollback.
        """
        ...

    # --- escrita -----------------------------------------------------------
    def execute(self, sql: str, params: Params = ()) -> int:
        """Executa um comando em transação e guarda o cursor dentro do adapter.

        As linhas de uma consulta são lidas por `fetch_*`.

        Args:
            sql: comando SQL, com marcadores de parâmetros.
            params: valores posicionais (sequência) ou nomeados (dict).

        Returns:
            int: número de linhas afetadas (-1 em consultas).
        """
        ...

    def execute_many(self, sql: str, params_seq: Sequence[Params]) -> int:
        """Executa o mesmo comando para vários conjuntos de parâmetros.

        Args:
            sql: comando SQL, com marcadores de parâmetros.
            params_seq: sequência de conjuntos de parâmetros.

        Returns:
            int: número de linhas afetadas.
        """
        ...

    def execute_script(self, script: str) -> None:
        """Executa um script com múltiplos comandos em transação.

        Args:
            script: texto SQL com vários comandos separados por ';'.

        Returns:
            None.
        """
        ...

    def insert(self, tabela: str, dados: dict[str, Any]) -> int:
        """Insere um registro e retorna o ID gerado.

        Args:
            tabela: nome da tabela (deve ser um valor confiável, não vindo do usuário).
            dados: mapa coluna -> valor a inserir.

        Returns:
            int: ID da linha inserida.
        """
        ...

    # --- leitura -----------------------------------------------------------
    def fetch_all(self) -> list[Linha]:
        """Consome o cursor do último `execute()` e devolve todas as linhas.

        Returns:
            list[Linha]: linhas como dicionários coluna -> valor (vazia se não houver).

        Raises:
            RuntimeError: se não há cursor ativo (nenhum `execute()` antes).
        """
        ...

    def fetch_one(self) -> Linha | None:
        """Consome a próxima linha do cursor do último `execute()`.

        Returns:
            Linha | None: linha como dicionário, ou None se não houver mais.

        Raises:
            RuntimeError: se não há cursor ativo.
        """
        ...

    def fetch_batches(self, tamanho_lote: int = 1000) -> Generator[list[Linha]]:
        """Consome o cursor do último `execute()` em lotes de até `tamanho_lote` linhas.

        Args:
            tamanho_lote: máximo de linhas por lote (>= 1).

        Yields:
            list[Linha]: cada lote de linhas.

        Raises:
            ValueError: se `tamanho_lote` < 1.
            RuntimeError: se não há cursor ativo.
        """
        ...

    # --- metadados ---------------------------------------------------------
    def table_exists(self, tabela: str) -> bool:
        """Indica se a tabela existe no banco.

        Args:
            tabela: nome da tabela.

        Returns:
            bool: True se a tabela existe.
        """
        ...
