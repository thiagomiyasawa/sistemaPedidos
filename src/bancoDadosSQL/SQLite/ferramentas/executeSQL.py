"""Toolbox para executar comandos SQL no bancoDados.db usando o SQLiteAdapter.

Uso como biblioteca:
    from executeSQL import executar, consultar, inserir

    executar("CREATE TABLE kpi (id INTEGER PRIMARY KEY, nome TEXT)")
    inserir("kpi", {"nome": "vendas"})
    linhas = consultar("SELECT * FROM kpi WHERE nome = ?", ("vendas",))

Uso pela linha de comando (a partir desta pasta):
    python executeSQL.py "SELECT * FROM kpi"
    python executeSQL.py "INSERT INTO kpi (nome) VALUES ('x')"
    python executeSQL.py --arquivo script.sql
    python executeSQL.py --tabelas
    python executeSQL.py --descrever kpi
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Generator, Sequence
from pathlib import Path
from typing import Any

# O adapter fica na pasta acima (sem pacote), então ela entra no sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from SQLiteAdapter import Params, SQLiteAdapter

# Comandos que devolvem linhas.
_PREFIXOS_CONSULTA = ("SELECT", "WITH", "PRAGMA", "EXPLAIN", "VALUES")


def _devolve_linhas(sql: str) -> bool:
    """Indica se o comando SQL é uma consulta que devolve linhas.

    Args:
        sql: comando SQL.

    Returns:
        bool: True se começar com SELECT, WITH, PRAGMA, EXPLAIN ou VALUES.
    """
    return sql.lstrip().upper().startswith(_PREFIXOS_CONSULTA)


# --- consultas -------------------------------------------------------------
def consultar(sql: str, params: Params = ()) -> list[dict[str, Any]]:
    """Executa um SELECT e devolve todas as linhas como dicionários.

    Args:
        sql: consulta SQL com marcadores.
        params: valores posicionais ou nomeados.

    Returns:
        list[dict[str, Any]]: linhas coluna -> valor.
    """
    with SQLiteAdapter() as db:
        return db.fetch_all(sql, params)


def consultar_um(sql: str, params: Params = ()) -> dict[str, Any] | None:
    """Executa um SELECT e devolve a primeira linha (ou None).

    Args:
        sql: consulta SQL com marcadores.
        params: valores posicionais ou nomeados.

    Returns:
        dict[str, Any] | None: primeira linha, ou None se vazio.
    """
    with SQLiteAdapter() as db:
        return db.fetch_one(sql, params)


def consultar_lotes(
    sql: str, params: Params = (), tamanho_lote: int = 1000
) -> Generator[list[dict[str, Any]]]:
    """Devolve o resultado de um SELECT em lotes, sem carregar tudo na memória.

    Args:
        sql: consulta SQL com marcadores.
        params: valores posicionais ou nomeados.
        tamanho_lote: máximo de linhas por lote (>= 1).

    Yields:
        list[dict[str, Any]]: cada lote de linhas.

    Raises:
        ValueError: se `tamanho_lote` < 1.
    """
    with SQLiteAdapter() as db:
        yield from db.fetch_batches(sql, params, tamanho_lote)


# --- escrita ---------------------------------------------------------------
def executar(sql: str, params: Params = ()) -> list[dict[str, Any]] | int:
    """Executa qualquer comando SQL.

    Retorna as linhas se o comando for uma consulta; caso contrário,
    o número de linhas afetadas.

    Args:
        sql: comando SQL com marcadores.
        params: valores posicionais ou nomeados.

    Returns:
        list[dict[str, Any]] | int: linhas (consultas) ou contagem de linhas afetadas.

    Raises:
        sqlite3.Error: em erro de SQL ou integridade.
    """
    with SQLiteAdapter() as db:
        if _devolve_linhas(sql):
            return db.fetch_all(sql, params)
        return db.execute(sql, params).rowcount


def executar_lote(sql: str, params_seq: Sequence[Params]) -> int:
    """Executa o mesmo comando para várias tuplas de parâmetros (executemany).

    Args:
        sql: comando SQL com marcadores.
        params_seq: sequência de conjuntos de parâmetros.

    Returns:
        int: número de linhas afetadas.
    """
    with SQLiteAdapter() as db:
        return db.execute_many(sql, params_seq)


def executar_script(script: str) -> None:
    """Executa um script com vários comandos separados por ';'.

    Args:
        script: texto SQL com um ou mais comandos.

    Returns:
        None.
    """
    with SQLiteAdapter() as db:
        db.execute_script(script)


def executar_arquivo(caminho: str | Path) -> None:
    """Executa um arquivo .sql inteiro.

    Args:
        caminho: caminho do arquivo .sql (lido em UTF-8).

    Returns:
        None.

    Raises:
        FileNotFoundError: se o arquivo não existir.
    """
    executar_script(Path(caminho).read_text(encoding="utf-8"))


def inserir(tabela: str, dados: dict[str, Any]) -> int:
    """Insere um registro e devolve o ID gerado.

    Args:
        tabela: nome da tabela (valor confiável).
        dados: mapa coluna -> valor.

    Returns:
        int: ID da linha inserida.
    """
    with SQLiteAdapter() as db:
        return db.insert(tabela, dados)


# --- metadados -------------------------------------------------------------
def tabela_existe(tabela: str) -> bool:
    """Indica se a tabela existe no banco.

    Args:
        tabela: nome da tabela.

    Returns:
        bool: True se existir.
    """
    with SQLiteAdapter() as db:
        return db.table_exists(tabela)


def listar_tabelas() -> list[str]:
    """Lista as tabelas do banco (exceto as internas `sqlite_*`), em ordem alfabética.

    Returns:
        list[str]: nomes das tabelas.
    """
    linhas = consultar(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [l["name"] for l in linhas]


def descrever_tabela(tabela: str) -> list[dict[str, Any]]:
    """Colunas da tabela (cid, name, type, notnull, dflt_value, pk).

    Args:
        tabela: nome de uma tabela existente.

    Returns:
        list[dict[str, Any]]: uma linha por coluna, no formato de `PRAGMA table_info`.

    Raises:
        ValueError: se a tabela não existir.
    """
    # PRAGMA não aceita parâmetros: o nome é validado contra as tabelas existentes.
    if not tabela_existe(tabela):
        raise ValueError(f"Tabela inexistente: {tabela}")
    return consultar(f'PRAGMA table_info("{tabela}")')


# --- linha de comando ------------------------------------------------------
def _imprimir(resultado: Any) -> None:
    """Imprime o resultado como JSON indentado (UTF-8; valores não serializáveis viram texto).

    Args:
        resultado: objeto a imprimir.

    Returns:
        None.
    """
    print(json.dumps(resultado, ensure_ascii=False, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da linha de comando.

    Args:
        argv: argumentos (sql, --arquivo, --tabelas, --descrever); None usa `sys.argv`.

    Returns:
        int: 0 em sucesso; 1 em erro (mensagem em stderr) ou se nenhum argumento for dado.
    """
    ap = argparse.ArgumentParser(description="Executa comandos SQL no bancoDados.db")
    ap.add_argument("sql", nargs="?", help="comando SQL a executar")
    ap.add_argument("-a", "--arquivo", help="executa um arquivo .sql")
    ap.add_argument("-t", "--tabelas", action="store_true", help="lista as tabelas")
    ap.add_argument("-d", "--descrever", metavar="TABELA", help="mostra as colunas")
    args = ap.parse_args(argv)

    try:
        if args.tabelas:
            _imprimir(listar_tabelas())
        elif args.descrever:
            _imprimir(descrever_tabela(args.descrever))
        elif args.arquivo:
            executar_arquivo(args.arquivo)
            print("Arquivo executado com sucesso.")
        elif args.sql:
            resultado = executar(args.sql)
            if isinstance(resultado, list):
                _imprimir(resultado)
            else:
                print(f"Linhas afetadas: {resultado}")
        else:
            ap.print_help()
            return 1
    except Exception as e:  # noqa: BLE001
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
