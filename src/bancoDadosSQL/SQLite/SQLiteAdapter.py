"""Adapter para banco de dados SQLite."""
from __future__ import annotations

import sqlite3
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Self

from ..dbAdapterInterface import Params, dbAdapterInterface
from dotenv import load_dotenv
import os
# O banco fica na mesma pasta deste arquivo.
load_dotenv()
CAMINHO_BANCO = os.getenv("SQLITE")


class SQLiteAdapter(dbAdapterInterface):
    """Encapsula a conexão e as operações básicas com o bancoDados.db.

    Uso:
        with SQLiteAdapter() as db:
            db.execute("CREATE TABLE kpi (id INTEGER PRIMARY KEY, nome TEXT)")
            db.execute("INSERT INTO kpi (nome) VALUES (?)", ("vendas",))
            db.execute("SELECT * FROM kpi")
            linhas = db.fetch_all()

    Attributes:
        caminho: caminho do arquivo do banco SQLite.
        timeout: segundos de espera por bloqueio do banco.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """Prepara o adapter sem abrir a conexão (aberta sob demanda).

        Args:
            timeout: segundos de espera por bloqueio do banco ao conectar.
        """
        self.caminho = str(CAMINHO_BANCO)
        self.timeout = timeout
        self._conn: sqlite3.Connection | None = None
        self._depth = 0  # nível de aninhamento de transaction()
        self._falhou = False  # True se algum bloco interno falhou na transação atual
        self._cursor: sqlite3.Cursor | None = None  # cursor do último execute()

    # --- conexão -----------------------------------------------------------
    def connect(self) -> sqlite3.Connection:
        """Abre (ou reutiliza) a conexão, com `row_factory` Row e chaves estrangeiras ligadas.

        Returns:
            sqlite3.Connection: conexão ativa.
        """
        if self._conn is None:
            self._conn = sqlite3.connect(self.caminho, timeout=self.timeout)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def close(self) -> None:
        """Fecha a conexão, se aberta.

        Returns:
            None.
        """
        self._cursor = None
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> Self:
        """Entra no contexto `with`, abrindo a conexão.

        Returns:
            Self: o próprio adapter.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando a conexão (não suprime exceções).

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None.
        """
        self.close()

    # --- transações --------------------------------------------------------
    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection]:
        """Commit ao sair normalmente, rollback em caso de exceção.

        Chamadas aninhadas participam da transação mais externa, que decide
        o commit/rollback.

        Yields:
            sqlite3.Connection: a conexão ativa.

        Raises:
            RuntimeError: se um bloco interno falhou e a exceção foi suprimida
                (a transação inteira é revertida).
            BaseException: repropaga qualquer exceção do bloco, após o rollback.
        """
        conn = self.connect()
        if self._depth > 0:
            # Já existe uma transação aberta: apenas participa dela.
            # O commit/rollback fica a cargo do bloco mais externo.
            try:
                yield conn
            except BaseException:
                self._falhou = True  # marca a transação inteira como comprometida
                raise
            return
        self._depth += 1
        self._falhou = False
        try:
            yield conn
            if self._falhou:
                raise RuntimeError(
                    "Transação revertida: um bloco interno falhou "
                    "e a exceção foi suprimida."
                )
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            self._depth -= 1
            self._falhou = False

    # --- operações ---------------------------------------------------------
    def execute(self, sql: str, params: Params = ()) -> int:
        """Executa um comando em transação e guarda o cursor dentro do adapter.

        O cursor é interno: as linhas de uma consulta são lidas por `fetch_*`.

        Args:
            sql: comando SQL com marcadores (`?` ou `:nome`).
            params: valores posicionais (sequência) ou nomeados (dict).

        Returns:
            int: número de linhas afetadas (-1 em consultas).

        Raises:
            sqlite3.Error: em erro de SQL ou integridade (após rollback).
        """
        with self.transaction() as conn:
            self._cursor = conn.execute(sql, params)
        return self._cursor.rowcount

    def execute_many(self, sql: str, params_seq: Sequence[Params]) -> int:
        """Executa o mesmo comando para vários conjuntos de parâmetros, em transação.

        Args:
            sql: comando SQL com marcadores.
            params_seq: sequência de conjuntos de parâmetros.

        Returns:
            int: número de linhas afetadas.

        Raises:
            sqlite3.Error: em erro de SQL ou integridade (após rollback).
        """
        with self.transaction() as conn:
            return conn.executemany(sql, params_seq).rowcount

    def execute_script(self, script: str) -> None:
        """Executa um script com vários comandos separados por ';'.

        Args:
            script: texto SQL com um ou mais comandos.

        Returns:
            None.

        Raises:
            sqlite3.Error: em erro de SQL (após rollback).
        """
        with self.transaction() as conn:
            conn.executescript(script)

    def _cursor_ativo(self) -> sqlite3.Cursor:
        """Devolve o cursor do último `execute()`.

        Returns:
            sqlite3.Cursor: cursor guardado no adapter.

        Raises:
            RuntimeError: se não houve `execute()` antes (ou o cursor já foi consumido/fechado).
        """
        if self._cursor is None:
            raise RuntimeError("Nenhum cursor ativo: chame execute() antes de fetch.")
        return self._cursor

    def fetch_all(self) -> list[dict[str, Any]]:
        """Consome o cursor do último `execute()` e devolve todas as linhas.

        Uso:
            db.execute("SELECT * FROM kpi WHERE nome = ?", ("vendas",))
            linhas = db.fetch_all()

        Returns:
            list[dict[str, Any]]: linhas coluna -> valor (vazia se nenhuma).

        Raises:
            RuntimeError: se não há cursor ativo.
        """
        return [dict(row) for row in self._cursor_ativo().fetchall()]

    def fetch_one(self) -> dict[str, Any] | None:
        """Consome a próxima linha do cursor do último `execute()`.

        Returns:
            dict[str, Any] | None: linha como dicionário, ou None se não houver mais.

        Raises:
            RuntimeError: se não há cursor ativo.
        """
        row = self._cursor_ativo().fetchone()
        return dict(row) if row else None

    def fetch_batches(
        self, tamanho_lote: int = 1000
    ) -> Generator[list[dict[str, Any]]]:
        """Consome o cursor do último `execute()` em lotes de até `tamanho_lote` linhas.

        Usa `fetchmany`, sem carregar tudo na memória:
            db.execute("SELECT * FROM kpi")
            for lote in db.fetch_batches(tamanho_lote=500):
                processar(lote)

        Args:
            tamanho_lote: máximo de linhas por lote (>= 1).

        Yields:
            list[dict[str, Any]]: cada lote de linhas.

        Raises:
            ValueError: se `tamanho_lote` < 1.
            RuntimeError: se não há cursor ativo.
        """
        if tamanho_lote < 1:
            raise ValueError("tamanho_lote deve ser >= 1")
        # Referência local: outro execute() durante a iteração troca self._cursor.
        cur = self._cursor_ativo()
        try:
            while lote := cur.fetchmany(tamanho_lote):
                yield [dict(row) for row in lote]
        finally:
            cur.close()
            if self._cursor is cur:
                self._cursor = None

    def insert(self, tabela: str, dados: dict[str, Any]) -> int:
        """Insere um registro e retorna o ID gerado.

        Args:
            tabela: nome da tabela (valor confiável; é interpolado no SQL).
            dados: mapa coluna -> valor a inserir.

        Returns:
            int: `lastrowid` da linha inserida.

        Raises:
            sqlite3.Error: em erro de SQL ou integridade (após rollback).
        """
        colunas = ", ".join(dados)
        marcadores = ", ".join(f":{c}" for c in dados)
        sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({marcadores})"
        with self.transaction() as conn:
            return conn.execute(sql, dados).lastrowid

    def table_exists(self, tabela: str) -> bool:
        """Indica se a tabela existe no banco.

        Args:
            tabela: nome da tabela.

        Returns:
            bool: True se existir em `sqlite_master`.
        """
        self.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tabela,)
        )
        return self.fetch_one() is not None
