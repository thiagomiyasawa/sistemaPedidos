"""Acesso a dados compartilhado pelas páginas de pedidos: filtros, requisições à API e ordem dos status."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from bancoDadosSQL.entidades.pedidos import Pedido
from client.adapters.interfaces.adapterAPIInterface import (
    ApiError,
)
from client.DIC import (
    DIC,
)  # DIC.facede_pedido() e DIC.facede_metricas()

TODOS = "Todos"
PERIODOS = {  # rótulo -> dias (None = sem limite)
    "Todo o período": None,
    "Últimos 7 dias": 7,
    "Últimos 30 dias": 30,
    "Últimos 90 dias": 90,
}
PERIODO_PADRAO = "Últimos 7 dias"  # filtro de período inicial: a semana
ORDEM_STATUS = [
    "novo",
    "em cotação",
    "aprovado",
    "em entrega",
    "entregue",
]  # ordem do processo


def chave_status(status: str) -> tuple[int, str]:
    """Chave de ordenação pela ordem do processo; status desconhecidos vão ao fim, em ordem alfabética.

    Args:
        status: Nome do status do pedido.

    Returns:
        Tupla (posição em `ORDEM_STATUS`, "") se conhecido; (tamanho de `ORDEM_STATUS`, status) se não.
    """
    try:
        return ORDEM_STATUS.index(status), ""
    except ValueError:
        return len(ORDEM_STATUS), status


_CHAVES_OPCOES = {
    "obra": "obras",
    "status_atual": "status",
    "origem": "origens",
}  # coluna -> chave da API
_cache_opcoes: dict[str, list[str]] = {}


def valores_distintos(coluna: str) -> list[str]:
    """Valores distintos de um atributo de `Pedido` (obra, status_atual, origem), lidos da API (em cache).

    Args:
        coluna: Atributo desejado: "obra", "status_atual" ou "origem".

    Returns:
        Lista de valores distintos (status ordenados pelo processo); lista vazia se a API falhar.

    Raises:
        AssertionError: Se `coluna` não for uma das colunas suportadas.
    """
    assert coluna in _CHAVES_OPCOES
    if not _cache_opcoes:
        try:  # uma só requisição traz as listas de todos os filtros
            valores = DIC.facede_metricas().valores_filtros()
        except ApiError:
            return []  # servidor indisponível: o erro aparece ao atualizar os gráficos
        for col, chave in _CHAVES_OPCOES.items():
            lista = valores[chave]
            _cache_opcoes[col] = (
                sorted(lista, key=chave_status) if col == "status_atual" else lista
            )
    return _cache_opcoes[coluna]


def tarefas_da_obra(obra: str) -> list[str]:
    """Tarefas distintas dos pedidos de uma obra (a obra é obrigatória: tarefa só existe dentro dela).

    Args:
        obra: Nome da obra (não pode ser vazio nem `TODOS`).

    Returns:
        Lista de tarefas da obra; lista vazia se a API falhar (`ApiError`).

    Raises:
        ValueError: Se a obra não for informada.
    """
    if not obra or obra == TODOS:
        raise ValueError("informe a obra para listar as tarefas")
    try:
        return DIC.facede_metricas().tarefas_da_obra(obra)
    except ApiError:
        return []


def filtrar_pedidos(filtros: dict) -> list[Pedido]:
    """Busca pedidos na API. `obra`/`status` filtram no servidor; o resto, aqui.

    Chaves: obra, status, origem, tarefa, dias (últimos N dias) ou de/ate (`date`, inclusivos).

    Args:
        filtros: Dicionário de filtros com as chaves acima; valores vazios ou `TODOS` são ignorados.

    Returns:
        Lista de `Pedido` que atendem aos filtros.

    Raises:
        ValueError: Se houver filtro de tarefa sem obra.
        ApiError: Se a consulta à API falhar.
    """

    def ativo(chave: str) -> str | None:
        """Valor do filtro `chave`, ou None se ausente, vazio ou igual a `TODOS`."""
        v = filtros.get(chave)
        return v if v and v != TODOS else None

    pedidos = DIC.facede_pedido().listar_todos(
        obra=ativo("obra"), status_atual=ativo("status")
    )
    if origem := ativo("origem"):
        pedidos = [p for p in pedidos if p.origem == origem]
    if tarefa := ativo("tarefa"):
        if not ativo("obra"):
            raise ValueError("filtrar por tarefa exige informar a obra")
        pedidos = [p for p in pedidos if p.tarefa == tarefa]
    if de := filtros.get("de"):
        pedidos = [p for p in pedidos if p.data_criacao and p.data_criacao.date() >= de]
    if ate := filtros.get("ate"):
        pedidos = [
            p for p in pedidos if p.data_criacao and p.data_criacao.date() <= ate
        ]
    if dias := filtros.get("dias"):
        # data_criacao vem do servidor em UTC (CURRENT_TIMESTAMP do SQLite), sem fuso.
        limite = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            days=int(dias)
        )
        pedidos = [p for p in pedidos if p.data_criacao and p.data_criacao >= limite]
    return pedidos


LIMITE_TOP_ITENS = (
    20  # o máximo que um gráfico de top itens pode pedir; ele corta no seu "Top N"
)


def top_itens(filtros: dict, limite: int = LIMITE_TOP_ITENS) -> list[tuple[str, int]]:
    """Itens mais solicitados (produto, quantidade total) com os mesmos filtros da página.

    Calculado no servidor pelo facade de métricas; aceita `obra`, `tarefa`, `status`, `origem`
    e o período (`dias` ou `de`/`ate`).

    Args:
        filtros: Dicionário de filtros da página; valores vazios ou `TODOS` são ignorados.
        limite: Quantidade máxima de itens retornados (padrão `LIMITE_TOP_ITENS`).

    Returns:
        Lista de tuplas (produto, quantidade total), do maior para o menor.

    Raises:
        ApiError: Se a consulta à API falhar.
    """

    def ativo(chave: str) -> str | None:
        """Valor do filtro `chave`, ou None se ausente, vazio ou igual a `TODOS`."""
        v = filtros.get(chave)
        return v if v and v != TODOS else None

    return DIC.facede_metricas().top_itens(
        obra=ativo("obra"),
        tarefa=ativo("tarefa"),
        status_atual=ativo("status"),
        origem=ativo("origem"),
        dias=filtros.get("dias"),
        de=filtros.get("de"),
        ate=filtros.get("ate"),
        limite=limite,
    )


@dataclass
class DadosPedidos:
    """O que a página entrega aos gráficos: pedidos já filtrados e, se pedido, o top de itens.

    Attributes:
        pedidos: Pedidos já filtrados.
        top_itens: Tuplas (produto, total), do maior para o menor; vazia se não solicitado.
    """

    pedidos: list[Pedido] = field(default_factory=list)
    top_itens: list[tuple[str, int]] = field(
        default_factory=list
    )  # (produto, total), do maior


def carregar_dados(filtros: dict, com_top_itens: bool = False) -> DadosPedidos:
    """Faz as requisições à API (uma vez por atualização) para todos os gráficos da página.

    Levanta `ApiError` se o servidor falhar. O top de itens só é buscado se algum gráfico
    precisar (`com_top_itens`).

    Args:
        filtros: Dicionário de filtros no formato de `filtrar_pedidos`.
        com_top_itens: Se True, busca também o top de itens.

    Returns:
        `DadosPedidos` com os pedidos filtrados e o top de itens (vazio se não pedido).

    Raises:
        ApiError: Se a API falhar.
    """
    return DadosPedidos(
        pedidos=filtrar_pedidos(filtros),
        top_itens=top_itens(filtros) if com_top_itens else [],
    )
