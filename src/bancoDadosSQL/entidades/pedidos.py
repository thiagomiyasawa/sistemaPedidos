"""Entidades `Pedido` e `ItemPedido`.

Cada entidade valida suas próprias regras. A persistência fica em
`facedePedido.FacedePedido`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import date, datetime
from typing import Any, Self


@dataclass
class ItemPedido:
    """Item de um pedido (um produto e sua quantidade).

    Attributes:
        produto: nome do produto (obrigatório, não vazio).
        quant: quantidade solicitada (> 0).
        data_necessidade: data em que o item é necessário; aceita texto ISO e converte.
        id_pedido: ID do pedido dono do item (None enquanto não persistido).
        id: número sequencial do item dentro do pedido (None enquanto não persistido).
    """

    produto: str
    quant: int
    data_necessidade: date | None = None
    id_pedido: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        """Converte `data_necessidade` de texto ISO e valida produto e quantidade.

        Returns:
            None.

        Raises:
            ValueError: se `produto` for vazio, `quant` <= 0 ou a data ISO for inválida.
        """
        if isinstance(self.data_necessidade, str):
            self.data_necessidade = date.fromisoformat(self.data_necessidade)
        if not self.produto.strip():
            raise ValueError("produto é obrigatório")
        if self.quant <= 0:
            raise ValueError("quant deve ser > 0")

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Self:
        """Constrói um item a partir de uma linha da tabela `item_pedido`.

        Args:
            row: mapa coluna -> valor, com id, id_pedido, produto, quant e data_necessidade.

        Returns:
            Self: o item correspondente.

        Raises:
            KeyError: se faltar alguma coluna esperada.
            ValueError: se os valores violarem as regras da entidade.
        """
        return cls(**{k: row[k] for k in ("id", "id_pedido", "produto", "quant", "data_necessidade")})

    def to_row(self) -> dict[str, Any]:
        """Converte o item para o formato da tabela `item_pedido`.

        Returns:
            dict[str, Any]: colunas -> valores, com `data_necessidade` em texto ISO (ou None).
        """
        d = asdict(self)
        d["data_necessidade"] = self.data_necessidade.isoformat() if self.data_necessidade else None
        return d


@dataclass
class Pedido:
    """Pedido de compra com seus itens e regras de validação.

    Attributes:
        num_itens: quantidade de itens do pedido (>= 0).
        status_atual: status corrente (obrigatório).
        origem: origem do pedido (obrigatório).
        local_entrega: local de entrega (obrigatório).
        obra: obra a que pertence (obrigatório).
        tarefa: tarefa dentro da obra (obrigatório).
        cod_rm: código do pedido no RM, se houver.
        user_id: id do usuário dono do pedido (None se sem dono, ex.: importado do RM).
        data_criacao: data/hora de criação; aceita texto ISO e converte.
        id: identificador (None enquanto não persistido).
        itens: lista de `ItemPedido` do pedido.
    """

    num_itens: int
    status_atual: str
    origem: str
    local_entrega: str
    obra: str
    tarefa: str
    cod_rm: int | None = None
    user_id: int | None = None
    data_criacao: datetime | None = None
    id: int | None = None
    itens: list[ItemPedido] = field(default_factory=list)

    _OBRIGATORIOS = ("status_atual", "origem", "local_entrega", "obra", "tarefa")

    def __post_init__(self) -> None:
        """Converte `data_criacao` de texto ISO e valida os campos obrigatórios.

        Returns:
            None.

        Raises:
            ValueError: se algum campo obrigatório for vazio, `num_itens` < 0
                ou a data ISO for inválida.
        """
        if isinstance(self.data_criacao, str):
            self.data_criacao = datetime.fromisoformat(self.data_criacao)
        for campo in self._OBRIGATORIOS:
            if not str(getattr(self, campo)).strip():
                raise ValueError(f"{campo} é obrigatório")
        if self.num_itens < 0:
            raise ValueError("num_itens não pode ser negativo")

    def adicionar_item(self, item: ItemPedido) -> None:
        """Adiciona um item ao pedido e atualiza `num_itens`.

        Args:
            item: item a adicionar.

        Returns:
            None.
        """
        self.itens.append(item)
        self.num_itens = len(self.itens)

    def mudar_status(self, novo: str) -> None:
        """Altera o status atual do pedido.

        Args:
            novo: novo status (não pode ser vazio).

        Returns:
            None.

        Raises:
            ValueError: se `novo` for vazio.
        """
        if not novo.strip():
            raise ValueError("status é obrigatório")
        self.status_atual = novo

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Self:
        """Constrói um pedido a partir de uma linha da tabela `pedido` (sem itens).

        Args:
            row: mapa coluna -> valor; colunas ausentes usam o padrão do campo.

        Returns:
            Self: o pedido correspondente, com `itens` vazio.

        Raises:
            ValueError: se os valores violarem as regras da entidade.
            TypeError: se faltar algum campo obrigatório sem padrão.
        """
        return cls(**{f.name: row[f.name] for f in fields(cls)
                      if f.name not in ("itens",) and f.name in row})

    def to_row(self) -> dict[str, Any]:
        """Colunas da tabela `pedido` (sem id/data_criacao quando ainda não definidos).

        Returns:
            dict[str, Any]: colunas -> valores; inclui `id` apenas se já definido
            e nunca inclui `data_criacao`.
        """
        d = {f: getattr(self, f) for f in
             ("cod_rm", "user_id", "num_itens", "status_atual", "origem", "local_entrega", "obra", "tarefa")}
        if self.id is not None:
            d["id"] = self.id
        return d

