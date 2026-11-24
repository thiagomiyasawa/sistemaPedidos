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
    """Item de um pedido (produto, quantidade e data de necessidade).

    Atributos:
        produto: nome do produto (obrigatório, não vazio).
        quant: quantidade solicitada (deve ser > 0).
        data_necessidade: data em que o item é necessário; aceita `date` ou
            string ISO (convertida), ou None.
        id_pedido: id do pedido ao qual pertence, ou None se ainda não vinculado.
        id: identificador do item no banco, ou None se ainda não persistido.
    """

    produto: str
    quant: int
    data_necessidade: date | None = None
    id_pedido: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        """Normaliza e valida o item após a criação.

        Converte `data_necessidade` de string ISO para `date`.

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
        """Cria um item a partir de uma linha do banco.

        Args:
            row: mapeamento com as chaves `id`, `id_pedido`, `produto`, `quant`
                e `data_necessidade`.

        Returns:
            Nova instância de `ItemPedido`.

        Raises:
            KeyError: se alguma chave obrigatória estiver ausente.
            ValueError: se os valores violarem as regras do item.
        """
        return cls(**{k: row[k] for k in ("id", "id_pedido", "produto", "quant", "data_necessidade")})

    def to_row(self) -> dict[str, Any]:
        """Converte o item em dicionário para persistência.

        Returns:
            Dicionário com todos os campos do item; `data_necessidade` vira
            string ISO (ou None).
        """
        d = asdict(self)
        d["data_necessidade"] = self.data_necessidade.isoformat() if self.data_necessidade else None
        return d


@dataclass
class Pedido:
    """Pedido de compra de uma obra, com seus itens.

    Atributos:
        num_itens: quantidade de itens (>= 0); atualizada em `adicionar_item`.
        status_atual: status corrente do pedido (obrigatório).
        origem: origem do pedido (obrigatório).
        local_entrega: local de entrega (obrigatório).
        obra: obra a que o pedido pertence (obrigatório).
        tarefa: tarefa associada (obrigatório).
        cod_rm: código do pedido no RM, ou None.
        data_criacao: data/hora de criação; aceita `datetime` ou string ISO, ou None.
        id: identificador no banco, ou None se ainda não persistido.
        itens: lista de `ItemPedido` do pedido.
    """

    num_itens: int
    status_atual: str
    origem: str
    local_entrega: str
    obra: str
    tarefa: str
    cod_rm: int | None = None
    data_criacao: datetime | None = None
    id: int | None = None
    itens: list[ItemPedido] = field(default_factory=list)

    _OBRIGATORIOS = ("status_atual", "origem", "local_entrega", "obra", "tarefa")

    def __post_init__(self) -> None:
        """Normaliza e valida o pedido após a criação.

        Converte `data_criacao` de string ISO para `datetime`.

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
            item: item a ser anexado à lista `itens`.

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
            ValueError: se `novo` for vazio ou só espaços.
        """
        if not novo.strip():
            raise ValueError("status é obrigatório")
        self.status_atual = novo

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Self:
        """Cria um pedido a partir de uma linha do banco.

        Args:
            row: mapeamento com as colunas do pedido; chaves ausentes usam o
                valor padrão do campo e `itens` é ignorado.

        Returns:
            Nova instância de `Pedido` (sem itens).

        Raises:
            TypeError: se faltar algum campo obrigatório sem padrão.
            ValueError: se os valores violarem as regras do pedido.
        """
        return cls(**{f.name: row[f.name] for f in fields(cls)
                      if f.name not in ("itens",) and f.name in row})

    def to_row(self) -> dict[str, Any]:
        """Colunas da tabela `pedido` (sem id/data_criacao quando ainda não definidos).

        Returns:
            Dicionário com `cod_rm`, `num_itens`, `status_atual`, `origem`,
            `local_entrega`, `obra`, `tarefa` e, se definido, `id`.
        """
        d = {f: getattr(self, f) for f in
             ("cod_rm", "num_itens", "status_atual", "origem", "local_entrega", "obra", "tarefa")}
        if self.id is not None:
            d["id"] = self.id
        return d

