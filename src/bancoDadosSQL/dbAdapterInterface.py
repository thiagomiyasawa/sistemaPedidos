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
            linhas = db.fetch_all("SELECT * FROM kpi")
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
    def execute(self, sql: str, params: Params = ()) -> Any:
        """Executa um comando em transação e devolve o cursor.

        Args:
            sql: comando SQL, com marcadores de parâmetros.
            params: valores posicionais (sequência) ou nomeados (dict).

        Returns:
            Any: cursor resultante (ex.: para ler `rowcount`).
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
    def fetch_all(self, sql: str, params: Params = ()) -> list[Linha]:
        """Devolve todas as linhas do resultado como dicionários.

        Args:
            sql: consulta SQL.
            params: valores posicionais ou nomeados da consulta.

        Returns:
            list[Linha]: linhas como dicionários coluna -> valor (vazia se não houver).
        """
        ...

    def fetch_one(self, sql: str, params: Params = ()) -> Linha | None:
        """Devolve a primeira linha do resultado, ou None se vazio.

        Args:
            sql: consulta SQL.
            params: valores posicionais ou nomeados da consulta.

        Returns:
            Linha | None: primeira linha como dicionário, ou None.
        """
        ...

    def fetch_batches(
        self, sql: str, params: Params = (), tamanho_lote: int = 1000
    ) -> Generator[list[Linha]]:
        """Devolve o resultado em lotes de até `tamanho_lote` linhas.

        Args:
            sql: consulta SQL.
            params: valores posicionais ou nomeados da consulta.
            tamanho_lote: máximo de linhas por lote (>= 1).

        Yields:
            list[Linha]: cada lote de linhas.

        Raises:
            ValueError: se `tamanho_lote` < 1.
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
