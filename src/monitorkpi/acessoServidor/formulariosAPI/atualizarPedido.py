"""PATCH /pedidos/{pedido_id} — campos a alterar (todos opcionais, ao menos um)."""
from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, model_validator

from bancoDadosSQL.entidades.pedidos import Pedido

from .saidaPedido import PedidoSaida
from .validacoes import CodRM, LocalEntrega, Obra, Origem, Status, Tarefa


class AtualizarPedidoEntrada(BaseModel):
    """Corpo do PATCH de um pedido: atualização parcial dos campos editáveis.

    Campos (todos opcionais, mas ao menos um deve ser enviado):
        cod_rm: Código do pedido no RM (pode ser nulo).
        status_atual: Novo status do pedido.
        origem: Nova origem do pedido.
        local_entrega: Novo local de entrega.
        obra: Nova obra.
        tarefa: Nova tarefa.
    """

    # `extra="forbid"` rejeita campos não editáveis (id, data_criacao, itens e
    # num_itens, que é derivado dos itens e não pode ser alterado à mão).
    model_config = ConfigDict(extra="forbid")

    cod_rm: CodRM | None = None
    status_atual: Status | None = None
    origem: Origem | None = None
    local_entrega: LocalEntrega | None = None
    obra: Obra | None = None
    tarefa: Tarefa | None = None

    @model_validator(mode="after")
    def _validar(self) -> Self:
        """Valida o conjunto de campos enviados.

        Returns:
            A própria instância, se válida.

        Raises:
            ValueError: Se nenhum campo foi informado ou se algum campo obrigatório
                no banco (todos, exceto `cod_rm`) foi enviado como nulo.
        """
        if not self.model_fields_set:
            raise ValueError("Nenhum campo informado")
        # Campos obrigatórios no banco não podem ser anulados com null.
        nulos = [c for c in self.model_fields_set
                 if c != "cod_rm" and getattr(self, c) is None]
        if nulos:
            raise ValueError(f"campos não podem ser nulos: {sorted(nulos)}")
        return self

    @classmethod
    def de_entidade(cls, pedido: Pedido) -> Self:
        """Monta (e valida) o corpo do PATCH com os campos editáveis do `Pedido`.

        Args:
            pedido: Entidade `Pedido` de origem.

        Returns:
            Nova instância com cod_rm, status_atual, origem, local_entrega, obra e tarefa.

        Raises:
            pydantic.ValidationError: Se os valores violarem as regras de validação.
        """
        return cls(
            cod_rm=pedido.cod_rm,
            status_atual=pedido.status_atual,
            origem=pedido.origem,
            local_entrega=pedido.local_entrega,
            obra=pedido.obra,
            tarefa=pedido.tarefa,
        )

    def para_json(self) -> dict[str, Any]:
        """Corpo JSON pronto para enviar.

        Returns:
            Dicionário serializável em JSON, apenas com os campos informados.
        """
        return self.model_dump(mode="json", exclude_unset=True)

    def campos(self) -> dict[str, Any]:
        """Somente os campos enviados pelo cliente.

        Returns:
            Dicionário nome do campo -> valor, apenas dos campos informados.
        """
        return self.model_dump(exclude_unset=True)


AtualizarPedidoSaida = PedidoSaida