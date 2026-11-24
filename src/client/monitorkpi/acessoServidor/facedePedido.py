"""Facade de pedidos sobre a API HTTP.

`FacedePedidoAPI` satisfaz o mesmo contrato `facedePedidoInterface` do facade SQL
(`bancoDadosSQL.facedes.facedePedido`), então a interface gráfica pode trocar uma
implementação pela outra. Ele fala com o servidor pelo `adapterAPIInterface`
(injetado; por padrão `AdapterAPI`). A conversão entre entidades (`Pedido`/`ItemPedido`)
e JSON, com validação, fica nos formulários de `formulariosAPI`.

Uso:
    with FacedePedidoAPI() as facede:
        pedidos = facede.listar(obra="Subestação Alfa")
        pedido = facede.obter(1)
        pedido.mudar_status("entregue")
        facede.salvar(pedido)
"""

from __future__ import annotations

from typing import Self

from bancoDadosSQL.entidades.pedidos import ItemPedido, Pedido
from client.monitorkpi.acessoServidor.adapterAPI import AdapterAPI
from client.monitorkpi.acessoServidor.formulariosAPI import listarItens
from client.monitorkpi.acessoServidor.formulariosAPI import listarPedidos
from client.monitorkpi.acessoServidor.formulariosAPI.adicionarItem import (
    AdicionarItemEntrada,
)
from client.monitorkpi.acessoServidor.formulariosAPI.atualizarPedido import (
    AtualizarPedidoEntrada,
)
from client.monitorkpi.acessoServidor.formulariosAPI.criarPedido import (
    CriarPedidoEntrada,
    CriarPedidoSaida,
)
from client.monitorkpi.acessoServidor.formulariosAPI.listarPedidos import (
    ListarPedidosEntrada,
)
from client.monitorkpi.acessoServidor.formulariosAPI.obterPedido import ObterPedidoSaida
from client.monitorkpi.acessoServidor.interfaces.adapterAPIInterface import (
    ApiError,
    Json,
    adapterAPIInterface,
)
from client.monitorkpi.acessoServidor.interfaces.facedePedidoAPIInterface import (
    facedePedidoAPIInterface,
)

_NAO_ENCONTRADO = 404


class FacedePedidoAPI(facedePedidoAPIInterface):
    """Facade de pedidos que persiste e consulta via API HTTP.

    Atributos:
        api: adapter de transporte usado nas requisições.
    """

    def __init__(self, api: adapterAPIInterface | None = None) -> None:
        """Inicializa o facade.

        Args:
            api: adapter HTTP a usar; se None cria um `AdapterAPI` padrão.
        """
        self.api: adapterAPIInterface = api or AdapterAPI()

    # --- ciclo de vida: fecha o adapter ------------------------------------
    def close(self) -> None:
        """Fecha o adapter e libera a conexão.

        Returns:
            None.
        """
        self.api.close()

    def __enter__(self) -> Self:
        """Entra no contexto `with`.

        Returns:
            O próprio facade.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o facade.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None (exceções não são suprimidas).
        """
        self.close()

    # --- leitura -----------------------------------------------------------
    def health(self) -> Json:
        """Estado do servidor e das tabelas.

        Returns:
            JSON da rota `/health` (status geral e situação das tabelas).

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        return self.api.get("/health")

    def obter(self, pedido_id: int, com_itens: bool = True) -> Pedido | None:
        """Busca um pedido pelo id.

        Args:
            pedido_id: identificador do pedido.
            com_itens: se False, devolve o pedido com a lista de itens vazia.

        Returns:
            O `Pedido` encontrado, ou None se a API responder 404.

        Raises:
            ApiError: em falha de comunicação ou erro HTTP diferente de 404.
        """
        try:
            dados = self.api.get(f"/pedidos/{pedido_id}")
        except ApiError as e:
            if e.status_code == _NAO_ENCONTRADO:
                return None
            raise
        pedido = ObterPedidoSaida.model_validate(dados).para_entidade()
        if not com_itens:
            pedido.itens = []
        return pedido

    def listar(
        self,
        obra: str | None = None,
        status_atual: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Pedido]:
        """Lista pedidos de forma paginada.

        Args:
            obra: filtra por obra, ou None.
            status_atual: filtra por status, ou None.
            limit: tamanho máximo da página.
            offset: quantidade de registros a pular.

        Returns:
            Lista de `Pedido` da página solicitada.

        Raises:
            ValueError: se os filtros forem inválidos (validação do formulário).
            ApiError: em falha de comunicação com a API.
        """
        filtro = ListarPedidosEntrada(
            obra=obra, status_atual=status_atual, limit=limit, offset=offset
        )
        return listarPedidos.para_entidades(self.api.get("/pedidos", **filtro.params()))

    def listar_todos(
        self,
        obra: str | None = None,
        status_atual: str | None = None,
        tamanho_pagina: int = 1000,
    ) -> list[Pedido]:
        """Todos os pedidos do filtro, percorrendo a paginação.

        Args:
            obra: filtra por obra, ou None.
            status_atual: filtra por status, ou None.
            tamanho_pagina: quantidade de pedidos pedida por requisição.

        Returns:
            Lista completa de `Pedido` que casam com o filtro.

        Raises:
            ApiError: em falha de comunicação com a API.
        """
        todos: list[Pedido] = []
        while True:
            lote = self.listar(
                obra, status_atual, limit=tamanho_pagina, offset=len(todos)
            )
            todos.extend(lote)
            if len(lote) < tamanho_pagina:
                return todos

    def itens_do_pedido(self, pedido_id: int) -> list[ItemPedido]:
        """Lista os itens de um pedido.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            Lista de `ItemPedido`; vazia se o pedido não existir (404).

        Raises:
            ApiError: em falha de comunicação ou erro HTTP diferente de 404.
        """
        try:
            return listarItens.para_entidades(
                self.api.get(f"/pedidos/{pedido_id}/itens")
            )
        except ApiError as e:
            if e.status_code == _NAO_ENCONTRADO:
                return []
            raise

    # --- escrita -----------------------------------------------------------
    def salvar(self, pedido: Pedido) -> Pedido:
        """Cria (id None) ou atualiza o pedido; itens sem id são enviados como novos.

        Args:
            pedido: entidade a persistir.

        Returns:
            O `Pedido` como salvo pelo servidor (com ids atribuídos).

        Raises:
            ApiError: em falha de comunicação ou resposta de erro da API.
        """
        if pedido.id is None:
            corpo = CriarPedidoEntrada.de_entidade(pedido).para_json()
            return CriarPedidoSaida.model_validate(
                self.api.post("/pedidos", json=corpo)
            ).para_entidade()

        corpo = AtualizarPedidoEntrada.de_entidade(pedido).para_json()
        salvo = self.api.patch(f"/pedidos/{pedido.id}", json=corpo)
        for item in pedido.itens:
            if item.id is None:
                novo = AdicionarItemEntrada.de_entidade(item).para_json()
                salvo = self.api.post(f"/pedidos/{pedido.id}/itens", json=novo)
        return ObterPedidoSaida.model_validate(salvo).para_entidade()

    def remover(self, pedido_id: int) -> bool:
        """Remove um pedido.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            True se removido; False se o pedido não existia (404).

        Raises:
            ApiError: em falha de comunicação ou erro HTTP diferente de 404.
        """
        try:
            self.api.delete(f"/pedidos/{pedido_id}")
        except ApiError as e:
            if e.status_code == _NAO_ENCONTRADO:
                return False
            raise
        return True
