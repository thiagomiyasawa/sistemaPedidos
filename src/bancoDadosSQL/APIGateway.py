"""API Gateway (FastAPI) para acesso HTTP aos pedidos.

A classe `APIGateway` envolve a aplicação FastAPI: valida entrada e saída com os
formulários de `formulariosAPI`, converte para as entidades `Pedido`/`ItemPedido`
e delega a persistência ao facade (`facedePedidoInterface`), que é injetado
(por padrão, via `DIC`).

Executar: rodar este arquivo (`python src/bancoDadosSQL/APIGateway.py`).
Interface de dev (modo dev, padrão): Swagger em http://127.0.0.1:8000/docs e ReDoc em /redoc.
Em produção, defina MONITORKPI_ENV=producao para desligá-las.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, FastAPI, HTTPException, Query, Response, status

if not __package__:  # executado como script: coloca `src` no sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bancoDadosSQL.DIC import DIC
from bancoDadosSQL.dbAdapterInterface import dbAdapterInterface
from bancoDadosSQL.entidades.pedidos import Pedido
from bancoDadosSQL.facedes.interfaces.facedeMetricasInterface import facedeMetricasInterface
from bancoDadosSQL.facedes.interfaces.facedePedidoInterface import facedePedidoInterface
from bancoDadosSQL.formulariosAPI.adicionarItem import AdicionarItemEntrada, AdicionarItemSaida
from bancoDadosSQL.formulariosAPI.atualizarPedido import AtualizarPedidoEntrada, AtualizarPedidoSaida
from bancoDadosSQL.formulariosAPI.criarPedido import CriarPedidoEntrada, CriarPedidoSaida
from bancoDadosSQL.formulariosAPI.health import HealthSaida
from bancoDadosSQL.formulariosAPI.listarItens import ListarItensSaida
from bancoDadosSQL.formulariosAPI.listarPedidos import ListarPedidosEntrada, ListarPedidosSaida
from bancoDadosSQL.formulariosAPI.obterPedido import ObterPedidoSaida
from bancoDadosSQL.formulariosAPI.saidaPedido import ItemPedidoSaida, PedidoSaida
from bancoDadosSQL.formulariosAPI.topItens import ItemTopSaida, TopItensEntrada, TopItensSaida
from bancoDadosSQL.formulariosAPI.valoresFiltros import TarefasEntrada, TarefasSaida, ValoresFiltrosSaida
from bancoDadosSQL.formulariosAPI.validacoes import ConflitoIntegridade, IdPedido


def ambiente_dev() -> bool:
    """True, exceto quando a variável de ambiente MONITORKPI_ENV for "producao".

    Returns:
        bool: True em modo dev (docs habilitadas e reload); False em produção.
    """
    return os.environ.get("MONITORKPI_ENV", "dev").strip().lower() != "producao"


class APIGateway:
    """Encapsula a aplicação FastAPI e o registro das rotas.

    Uso:
        gateway = APIGateway()          # usa o facade/db do DIC
        gateway.app                     # aplicação ASGI
        gateway.run()                   # sobe o servidor

    Responsabilidade: expor os pedidos, itens e métricas via HTTP, traduzindo
    erros de domínio em respostas HTTP e delegando a persistência aos facades.

    Attributes:
        dev (bool): True se a interface de documentação (Swagger/ReDoc) está ativa.
        app (FastAPI): aplicação ASGI com as rotas registradas.
    """

    def __init__(
        self,
        facede_factory: Callable[[], facedePedidoInterface] = DIC.facede_pedido,
        db_factory: Callable[[], dbAdapterInterface] = DIC.db,
        metricas_factory: Callable[[], facedeMetricasInterface] = DIC.facede_metricas,
        titulo: str = "monitorKPI API Gateway",
        dev: bool | None = None,
    ) -> None:
        """Cria a aplicação FastAPI e registra as rotas.

        Args:
            facede_factory: fábrica que devolve um facade de pedidos novo por chamada.
            db_factory: fábrica que devolve um adapter de banco novo por chamada.
            metricas_factory: fábrica que devolve um facade de métricas novo por chamada.
            titulo: título exibido na documentação da API.
            dev: força modo dev (True) ou produção (False); None usa `ambiente_dev()`.
        """
        # Fábricas (não instâncias): cada requisição cria o seu facade/conexão,
        # pois a conexão SQLite é presa à thread do endpoint.
        self._facede_factory = facede_factory
        self._db_factory = db_factory
        self._metricas_factory = metricas_factory
        # Interface de dev (Swagger UI em /docs, ReDoc em /redoc e /openapi.json):
        # ligada por padrão; desligue com MONITORKPI_ENV=producao (ou dev=False).
        self.dev = ambiente_dev() if dev is None else dev
        self.app = FastAPI(
            title=titulo,
            version="0.1.0",
            docs_url="/docs" if self.dev else None,
            redoc_url="/redoc" if self.dev else None,
            openapi_url="/openapi.json" if self.dev else None,
        )
        self._registrar_rotas()

    # --- infraestrutura ------------------------------------------------------
    def _facede(self):
        """Facade de pedidos novo (ver `_sessao`).

        Returns:
            Context manager que entrega um facade de pedidos e fecha a conexão ao sair.
        """
        return self._sessao(self._facede_factory)

    @contextmanager
    def _sessao(self, factory: Callable[[], Any]) -> Generator[Any]:
        """Entrega um facade novo; traduz erros de domínio em HTTP e fecha a conexão.

        Args:
            factory: fábrica sem argumentos que cria o facade (e sua conexão).

        Yields:
            O facade criado pela fábrica.

        Raises:
            HTTPException: 409 para `ConflitoIntegridade` e `sqlite3.IntegrityError`;
                422 para `ValueError`.
        """
        f = factory()
        try:
            yield f
        except ConflitoIntegridade as e:  # formulário: violaria a integridade do que já existe
            raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e
        except ValueError as e:  # regra de validação da entidade
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
        except sqlite3.IntegrityError as e:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Violação de integridade: {e}") from e
        finally:
            close = getattr(getattr(f, "db", None), "close", None)
            if close:
                close()

    @staticmethod
    def _obter_ou_404(f: facedePedidoInterface, pedido_id: IdPedido, com_itens: bool = True) -> Pedido:
        """Obtém um pedido ou falha com 404.

        Args:
            f: facade de pedidos.
            pedido_id: identificador do pedido.
            com_itens: se True, carrega também os itens do pedido.

        Returns:
            Pedido: o pedido encontrado.

        Raises:
            HTTPException: 404 se o pedido não existir.
        """
        pedido = f.obter(pedido_id, com_itens)
        if pedido is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado")
        return pedido

    # --- rotas ---------------------------------------------------------------
    def _registrar_rotas(self) -> None:
        """Registra no `app` as rotas de infra, pedidos, itens e filtros.

        Returns:
            None.
        """
        self.app.add_api_route("/health", self.health, methods=["GET"], tags=["infra"])

        r = APIRouter(prefix="/pedidos", tags=["pedidos"])
        r.add_api_route("", self.listar_pedidos, methods=["GET"])
        r.add_api_route("", self.criar_pedido, methods=["POST"],
                        status_code=status.HTTP_201_CREATED)
        r.add_api_route("/{pedido_id}", self.obter_pedido, methods=["GET"])
        r.add_api_route("/{pedido_id}", self.atualizar_pedido, methods=["PATCH"])
        r.add_api_route("/{pedido_id}", self.remover_pedido, methods=["DELETE"],
                        status_code=status.HTTP_204_NO_CONTENT)
        r.add_api_route("/{pedido_id}/itens", self.listar_itens, methods=["GET"])
        r.add_api_route("/{pedido_id}/itens", self.adicionar_item, methods=["POST"],
                        status_code=status.HTTP_201_CREATED)
        self.app.include_router(r)

        ri = APIRouter(prefix="/itens", tags=["itens"])
        ri.add_api_route("/top", self.top_itens, methods=["GET"])
        self.app.include_router(ri)

        self.app.add_api_route("/filtros", self.valores_filtros, methods=["GET"], tags=["itens"])
        self.app.add_api_route("/filtros/tarefas", self.tarefas_da_obra, methods=["GET"], tags=["itens"])

    def health(self) -> HealthSaida:
        """Verifica a saúde da API e a existência das tabelas `pedido` e `item_pedido`.

        Returns:
            HealthSaida: status "ok" e mapa tabela -> existe.
        """
        with self._db_factory() as db:
            return HealthSaida(status="ok", tabelas={
                t: db.table_exists(t) for t in ("pedido", "item_pedido")})

    def listar_pedidos(
        self, filtros: Annotated[ListarPedidosEntrada, Query()]
    ) -> ListarPedidosSaida:
        """Lista pedidos com filtros opcionais e paginação.

        Args:
            filtros: parâmetros de query (obra, status_atual, limit, offset).

        Returns:
            ListarPedidosSaida: lista de pedidos (sem itens).
        """
        with self._facede() as f:
            pedidos = f.listar(filtros.obra, filtros.status_atual, filtros.limit, filtros.offset)
            return [PedidoSaida.model_validate(p) for p in pedidos]

    def valores_filtros(self) -> ValoresFiltrosSaida:
        """Obras, status e origens existentes, para montar os filtros das telas.

        Returns:
            ValoresFiltrosSaida: valores distintos de obras, status e origens.
        """
        with self._sessao(self._metricas_factory) as f:
            return ValoresFiltrosSaida(**f.valores_filtros())

    def tarefas_da_obra(self, filtros: Annotated[TarefasEntrada, Query()]) -> TarefasSaida:
        """Tarefas de uma obra (a obra é obrigatória: tarefa só existe dentro dela).

        Args:
            filtros: parâmetros de query com a obra.

        Returns:
            TarefasSaida: tarefas distintas da obra.

        Raises:
            HTTPException: 422 se a obra for vazia.
        """
        with self._sessao(self._metricas_factory) as f:
            return f.tarefas_da_obra(filtros.obra)

    def top_itens(self, filtros: Annotated[TopItensEntrada, Query()]) -> TopItensSaida:
        """Itens mais solicitados (soma de quantidade por produto), só o top `limite`.

        Args:
            filtros: parâmetros de query (obra, tarefa, status_atual, origem, período, limite).

        Returns:
            TopItensSaida: lista de (produto, quantidade) do maior para o menor.

        Raises:
            HTTPException: 422 se filtrar por tarefa sem informar a obra.
        """
        desde, ate = filtros.periodo()
        with self._sessao(self._metricas_factory) as f:
            top = f.top_itens(filtros.obra, filtros.tarefa, filtros.status_atual,
                              filtros.origem, desde, ate, filtros.limite)
            return [ItemTopSaida(produto=p, quantidade=q) for p, q in top]

    def criar_pedido(self, corpo: CriarPedidoEntrada, response: Response) -> CriarPedidoSaida:
        """Cria um pedido e define o cabeçalho `Location` com a sua URL.

        Args:
            corpo: dados do pedido a criar.
            response: resposta HTTP, onde o cabeçalho `Location` é gravado.

        Returns:
            CriarPedidoSaida: pedido criado (status 201).

        Raises:
            HTTPException: 409/422 por conflito de integridade ou validação.
        """
        with self._facede() as f:
            pedido = f.salvar(corpo.para_entidade())
            response.headers["Location"] = f"/pedidos/{pedido.id}"
            return PedidoSaida.model_validate(pedido)

    def obter_pedido(self, pedido_id: IdPedido) -> ObterPedidoSaida:
        """Obtém um pedido com seus itens.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            ObterPedidoSaida: pedido encontrado.

        Raises:
            HTTPException: 404 se não existir.
        """
        with self._facede() as f:
            return PedidoSaida.model_validate(self._obter_ou_404(f, pedido_id))

    def atualizar_pedido(
        self, pedido_id: IdPedido, corpo: AtualizarPedidoEntrada
    ) -> AtualizarPedidoSaida:
        """Atualiza parcialmente um pedido (PATCH), revalidando as regras da entidade.

        Args:
            pedido_id: identificador do pedido.
            corpo: campos a alterar (apenas os informados).

        Returns:
            AtualizarPedidoSaida: pedido após a atualização.

        Raises:
            HTTPException: 404 se não existir; 409/422 por integridade ou validação.
        """
        with self._facede() as f:
            pedido = self._obter_ou_404(f, pedido_id, com_itens=False)
            # Reconstrói a entidade para que as regras de validação sejam reaplicadas.
            atual = {k: v for k, v in asdict(pedido).items() if k != "itens"}
            salvo = f.salvar(Pedido(**{**atual, **corpo.campos()}))
            return PedidoSaida.model_validate(salvo)

    def remover_pedido(self, pedido_id: IdPedido) -> None:
        """Remove um pedido e seus itens.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            None (status 204).

        Raises:
            HTTPException: 404 se o pedido não existir.
        """
        with self._facede() as f:
            if not f.remover(pedido_id):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado")

    def listar_itens(self, pedido_id: IdPedido) -> ListarItensSaida:
        """Lista os itens de um pedido.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            ListarItensSaida: itens do pedido.

        Raises:
            HTTPException: 404 se o pedido não existir.
        """
        with self._facede() as f:
            self._obter_ou_404(f, pedido_id, com_itens=False)
            return [ItemPedidoSaida.model_validate(i) for i in f.itens_do_pedido(pedido_id)]

    def adicionar_item(self, pedido_id: IdPedido, corpo: AdicionarItemEntrada) -> AdicionarItemSaida:
        """Adiciona um item a um pedido existente.

        Args:
            pedido_id: identificador do pedido.
            corpo: dados do novo item.

        Returns:
            AdicionarItemSaida: pedido atualizado com o item (status 201).

        Raises:
            HTTPException: 404 se o pedido não existir; 409 se violar limite de
                itens ou duplicidade; 422 por validação.
        """
        with self._facede() as f:
            pedido = self._obter_ou_404(f, pedido_id)
            corpo.verificar(pedido)  # integridade: limite de itens e duplicidade
            pedido.itens = [corpo.para_entidade()]  # só o item novo é inserido
            pedido.num_itens += 1
            f.salvar(pedido)
            return PedidoSaida.model_validate(self._obter_ou_404(f, pedido_id))

    # --- execução ------------------------------------------------------------
    @staticmethod
    def run(host: str = "127.0.0.1", port: int = 8000, reload: bool | None = None) -> None:
        """Sobe o servidor. Usa o `app` do módulo (necessário para o `reload`).

        Em modo dev (padrão) liga o `reload` e a interface de docs.

        Args:
            host: endereço de escuta.
            port: porta de escuta.
            reload: recarrega ao alterar o código; None usa `ambiente_dev()`.

        Returns:
            None; bloqueia enquanto o servidor estiver em execução.
        """
        import uvicorn

        if reload is None:
            reload = ambiente_dev()

        uvicorn.run("bancoDadosSQL.APIGateway:app", host=host, port=port, reload=reload)


# Instância padrão exposta para o servidor ASGI (`uvicorn bancoDadosSQL.APIGateway:app`).
gateway = APIGateway()
app = gateway.app


def main() -> None:
    """Ponto de entrada: sobe o servidor com `APIGateway.run()`.

    Returns:
        None.
    """
    APIGateway.run()


if __name__ == "__main__":
    main()
