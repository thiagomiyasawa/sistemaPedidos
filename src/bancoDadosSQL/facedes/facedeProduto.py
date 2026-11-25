"""Facade de produtos: leitura do catálogo (tabela `produtos`), paginada e com filtros.

Depende apenas de `dbAdapterInterface`.

Uso:
    with DIC.db() as db:
        f = FacedeProduto(db)
        pagina = f.listar(busca="cabo", limit=30, offset=0)
        total = f.contar(busca="cabo")
"""
from __future__ import annotations

from typing import Any

from ..dbAdapterInterface import dbAdapterInterface
from .interfaces.facedeProdutoInterface import facedeProdutoInterface


class FacedeProduto(facedeProdutoInterface):
    """Implementação SQL da leitura do catálogo de produtos.

    Attributes:
        db: adapter de banco usado para executar as consultas.
    """

    def __init__(self, db: dbAdapterInterface) -> None:
        """Inicializa o facade com o adapter de banco.

        Args:
            db: adapter que satisfaz `dbAdapterInterface`.
        """
        self.db = db

    @staticmethod
    def _filtro(busca: str | None, categoria: str | None) -> tuple[str, list]:
        """Cláusula WHERE comum a `listar` e `contar`, e seus parâmetros.

        A busca escapa `%`, `_` e `\\`, para valerem como texto comum.

        Args:
            busca: texto procurado no código ou na descrição, se informado.
            categoria: categoria exata, se informada.

        Returns:
            tuple[str, list]: cláusula WHERE (vazia se sem filtros) e lista de parâmetros.
        """
        condicoes, params = [], []
        if categoria:
            condicoes.append("categoria = ?")
            params.append(categoria)
        if busca:
            like = "%" + busca.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            condicoes.append("(codigo LIKE ? ESCAPE '\\' OR descricao LIKE ? ESCAPE '\\')")
            params += [like, like]
        return ("WHERE " + " AND ".join(condicoes)) if condicoes else "", params

    def listar(self, busca: str | None = None, categoria: str | None = None,
               limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Uma página de produtos, ordenados por categoria e código.

        Args:
            busca: texto procurado no código ou na descrição, se informado.
            categoria: filtra por categoria exata, se informada.
            limit: máximo de produtos retornados.
            offset: quantidade de produtos a pular.

        Returns:
            list[dict[str, Any]]: produtos com `id`, `codigo`, `descricao` e `categoria`.
        """
        where, params = self._filtro(busca, categoria)
        linhas = self.db.fetch_all(
            f"SELECT id, codigo, descricao, categoria FROM produtos {where} "
            "ORDER BY categoria, codigo, id LIMIT ? OFFSET ?",
            [*params, limit, offset],
        )
        return [dict(linha) for linha in linhas]

    def contar(self, busca: str | None = None, categoria: str | None = None) -> int:
        """Quantos produtos casam com o filtro (para calcular o número de páginas).

        Args:
            busca: texto procurado no código ou na descrição, se informado.
            categoria: filtra por categoria exata, se informada.

        Returns:
            int: total de produtos que casam com o filtro.
        """
        where, params = self._filtro(busca, categoria)
        return self.db.fetch_one(f"SELECT COUNT(*) AS n FROM produtos {where}", params)["n"]

    def categorias(self) -> list[str]:
        """Categorias distintas do catálogo, em ordem alfabética.

        Returns:
            list[str]: categorias (sem valores vazios).
        """
        linhas = self.db.fetch_all(
            "SELECT DISTINCT categoria FROM produtos "
            "WHERE categoria IS NOT NULL AND categoria <> '' ORDER BY categoria")
        return [linha["categoria"] for linha in linhas]
