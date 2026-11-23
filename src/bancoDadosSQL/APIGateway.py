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
from dataclasses import asdict, replace
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    Security,
    status,
)
from fastapi.security import APIKeyHeader

if not __package__:  # executado como script: coloca `src` no sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bancoDadosSQL.DIC import DIC
from bancoDadosSQL.dbAdapterInterface import dbAdapterInterface
from bancoDadosSQL.entidades.pedidos import Pedido
from bancoDadosSQL.facedes.facedeAutorizacao import (
    METRICAS_LER,
    PEDIDOS_ALTERAR,
    PEDIDOS_CRIAR,
    PEDIDOS_LER,
    PEDIDOS_REMOVER,
    PEDIDOS_TODOS,
    USUARIOS_GERENCIAR,
)
from bancoDadosSQL.facedes.interfaces.facedeAutorizacaoInterface import (
    facedeAutorizacaoInterface,
)
from bancoDadosSQL.facedes.interfaces.facedeAutenticacaoInterface import (
    Identidade,
    facedeAutenticacaoInterface,
)
from bancoDadosSQL.facedes.interfaces.facedeMetricasInterface import (
    facedeMetricasInterface,
)
from bancoDadosSQL.facedes.interfaces.facedePedidoInterface import facedePedidoInterface
from bancoDadosSQL.formulariosAPI.admin import (
    AtualizarUsuarioEntrada,
    IdUsuario,
    ListarUsuariosEntrada,
    PermissaoUsuarioEntrada,
    PermissoesSaida,
    UsuarioSaida,
)
from bancoDadosSQL.formulariosAPI.adicionarItem import (
    AdicionarItemEntrada,
    AdicionarItemSaida,
)
from bancoDadosSQL.formulariosAPI.atualizarPedido import (
    AtualizarPedidoEntrada,
    AtualizarPedidoSaida,
)
from bancoDadosSQL.formulariosAPI.criarPedido import (
    CriarPedidoEntrada,
    CriarPedidoSaida,
)
from bancoDadosSQL.formulariosAPI.health import HealthSaida
from bancoDadosSQL.formulariosAPI.login import (
    LoginEntrada,
    LoginSaida,
    RegistroEntrada,
    RegistroSaida,
)
from bancoDadosSQL.formulariosAPI.listarItens import ListarItensSaida
from bancoDadosSQL.formulariosAPI.listarPedidos import (
    ListarPedidosEntrada,
    ListarPedidosSaida,
)
from bancoDadosSQL.formulariosAPI.obterPedido import ObterPedidoSaida
from bancoDadosSQL.formulariosAPI.saidaPedido import ItemPedidoSaida, PedidoSaida
from bancoDadosSQL.formulariosAPI.topItens import (
    ItemTopSaida,
    TopItensEntrada,
    TopItensSaida,
)
from bancoDadosSQL.formulariosAPI.valoresFiltros import (
    TarefasEntrada,
    TarefasSaida,
    ValoresFiltrosSaida,
)
from bancoDadosSQL.formulariosAPI.validacoes import ConflitoIntegridade, IdPedido


def ambiente_dev() -> bool:
    """True, exceto quando a variável de ambiente MONITORKPI_ENV for "producao".

    Returns:
        bool: True em modo dev (docs habilitadas e reload); False em produção.
    """
    return os.environ.get("MONITORKPI_ENV", "dev").strip().lower() != "producao"


CABECALHO_API_KEY = "X-API-Key"
_esquema_api_key = APIKeyHeader(name=CABECALHO_API_KEY, auto_error=False)
# Rotas que dispensam a chave (é por elas que a chave é obtida).
ROTAS_PUBLICAS = frozenset({"/login", "/registro"})


def exige(permissao: str) -> Callable[..., None]:
    """Cria a dependência que exige uma permissão do usuário autenticado.

    Args:
        permissao: permissão necessária (ver `facedeAutorizacao.PERMISSOES`).

    Returns:
        Callable[..., None]: dependência do FastAPI; responde 403 se faltar a permissão.
    """

    def _verifica(ident: Annotated[Identidade, Depends(identidade_atual)]) -> None:
        if permissao not in ident.permissoes:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permissão insuficiente")

    return _verifica


def identidade_atual(request: Request) -> Identidade:
    """Dependência das rotas protegidas: o usuário autenticado na requisição.

    `APIGateway._autenticar` (dependência global) roda antes e grava a identidade
    em `request.state`.

    Args:
        request: requisição em curso.

    Returns:
        Identidade: dono da chave de API da requisição.

    Raises:
        HTTPException: 401 se não houver identidade (rota pública ou falha interna).
    """
    ident = getattr(request.state, "identidade", None)
    if ident is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Não autenticado")
    return ident


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
        autenticacao_factory: Callable[[], facedeAutenticacaoInterface] = DIC.facede_autenticacao,
        autorizacao_factory: Callable[[], facedeAutorizacaoInterface] = DIC.facede_autorizacao,
    ) -> None:
        """Cria a aplicação FastAPI e registra as rotas.

        Autenticação: todas as rotas (inclusive `/health`) exigem o cabeçalho
        `X-API-Key` com uma chave existente e não vencida na tabela `chavesAPI`
        (consultada pelo facade de autenticação a cada requisição).

        Args:
            facede_factory: fábrica que devolve um facade de pedidos novo por chamada.
            db_factory: fábrica que devolve um adapter de banco novo por chamada.
            metricas_factory: fábrica que devolve um facade de métricas novo por chamada.
            titulo: título exibido na documentação da API.
            dev: força modo dev (True) ou produção (False); None usa `ambiente_dev()`.
            autenticacao_factory: fábrica que devolve um facade de autenticação novo por chamada.
            autorizacao_factory: fábrica que devolve um facade de autorização novo por chamada.
        """
        self._autenticacao_factory = autenticacao_factory
        self._autorizacao_factory = autorizacao_factory
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
            # Global: roda em TODA rota registrada no app (inclusive futuras).
            dependencies=[Depends(self._autenticar)],
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
        except (
            ConflitoIntegridade
        ) as e:  # formulário: violaria a integridade do que já existe
            raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e
        except ValueError as e:  # regra de validação da entidade
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e)) from e
        except sqlite3.IntegrityError as e:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"Violação de integridade: {e}"
            ) from e
        finally:
            close = getattr(getattr(f, "db", None), "close", None)
            if close:
                close()

    def _autenticar(
        self, request: Request, chave: Annotated[str | None, Security(_esquema_api_key)] = None
    ) -> Identidade | None:
        """Dependência global que valida o cabeçalho `X-API-Key` (exceto em `ROTAS_PUBLICAS`).

        Grava a `Identidade` em `request.state` para `identidade_atual`.

        Args:
            request: requisição em curso.
            chave: valor do cabeçalho `X-API-Key`, ou None se ausente.

        Returns:
            Identidade | None: dono da chave, já com as permissões efetivas; None nas rotas públicas.

        Raises:
            HTTPException: 401 se a chave estiver ausente, inexistente, vencida ou
                de usuário inativo.
        """
        if request.url.path in ROTAS_PUBLICAS:
            return None
        with self._sessao(self._autenticacao_factory) as f:
            identidade = f.autenticar(chave)
        if identidade is None:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Chave de API inválida, vencida ou ausente",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        with self._sessao(self._autorizacao_factory) as a:
            identidade = replace(
                identidade, permissoes=a.permissoes(identidade.user_id, identidade.cargo))
        request.state.identidade = identidade
        return identidade

    @staticmethod
    def _admin(ident: Identidade) -> bool:
        """Indica se o usuário tem a permissão `pedidos:todos` (pedidos de qualquer dono).

        Args:
            ident: identidade do usuário autenticado.

        Returns:
            bool: True se `PEDIDOS_TODOS` está nas permissões efetivas.
        """
        return PEDIDOS_TODOS in ident.permissoes

    @staticmethod
    def _obter_ou_404(
        f: facedePedidoInterface,
        pedido_id: IdPedido,
        ident: Identidade,
        com_itens: bool = True,
    ) -> Pedido:
        """Obtém um pedido do usuário ou falha com 404.

        Pedido de outro usuário (ou sem dono) também dá 404 para quem não é admin,
        para não revelar que o id existe.

        Args:
            f: facade de pedidos.
            pedido_id: identificador do pedido.
            ident: usuário autenticado.
            com_itens: se True, carrega também os itens do pedido.

        Returns:
            Pedido: o pedido encontrado.

        Raises:
            HTTPException: 404 se o pedido não existir ou não for do usuário.
        """
        pedido = f.obter(pedido_id, com_itens)
        if pedido is None or not (
            APIGateway._admin(ident) or pedido.user_id == ident.user_id
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado")
        return pedido

    # --- rotas ---------------------------------------------------------------
    def _registrar_rotas(self) -> None:
        """Registra no `app` as rotas de infra, pedidos, itens e filtros.

        Returns:
            None.
        """
        self.app.add_api_route("/health", self.health, methods=["GET"], tags=["infra"])

        self.app.add_api_route("/login", self.login, methods=["POST"], tags=["auth"])
        self.app.add_api_route("/registro", self.registrar_usuario, methods=["POST"],
                               tags=["auth"], status_code=status.HTTP_201_CREATED)

        def perm(p: str) -> list[Any]:
            return [Depends(exige(p))]

        r = APIRouter(prefix="/pedidos", tags=["pedidos"])
        r.add_api_route("", self.listar_pedidos, methods=["GET"], dependencies=perm(PEDIDOS_LER))
        r.add_api_route("", self.criar_pedido, methods=["POST"], dependencies=perm(PEDIDOS_CRIAR),
                        status_code=status.HTTP_201_CREATED)
        r.add_api_route("/{pedido_id}", self.obter_pedido, methods=["GET"],
                        dependencies=perm(PEDIDOS_LER))
        r.add_api_route("/{pedido_id}", self.atualizar_pedido, methods=["PATCH"],
                        dependencies=perm(PEDIDOS_ALTERAR))
        r.add_api_route("/{pedido_id}", self.remover_pedido, methods=["DELETE"],
                        dependencies=perm(PEDIDOS_REMOVER), status_code=status.HTTP_204_NO_CONTENT)
        r.add_api_route("/{pedido_id}/itens", self.listar_itens, methods=["GET"],
                        dependencies=perm(PEDIDOS_LER))
        r.add_api_route("/{pedido_id}/itens", self.adicionar_item, methods=["POST"],
                        dependencies=perm(PEDIDOS_ALTERAR), status_code=status.HTTP_201_CREATED)
        self.app.include_router(r)

        ri = APIRouter(prefix="/itens", tags=["itens"])
        ri.add_api_route("/top", self.top_itens, methods=["GET"], dependencies=perm(METRICAS_LER))
        self.app.include_router(ri)

        self.app.add_api_route("/filtros", self.valores_filtros, methods=["GET"],
                               tags=["itens"], dependencies=perm(METRICAS_LER))
        self.app.add_api_route("/filtros/tarefas", self.tarefas_da_obra, methods=["GET"],
                               tags=["itens"], dependencies=perm(METRICAS_LER))

        # Administração de usuários e permissões: exige `usuarios:gerenciar`.
        ra = APIRouter(prefix="/admin/usuarios", tags=["admin"],
                       dependencies=perm(USUARIOS_GERENCIAR))
        ra.add_api_route("", self.listar_usuarios, methods=["GET"])
        ra.add_api_route("/{user_id}", self.atualizar_usuario, methods=["PATCH"])
        ra.add_api_route("/{user_id}/permissoes", self.permissoes_do_usuario, methods=["GET"])
        ra.add_api_route("/{user_id}/permissoes/{permissao}", self.definir_permissao,
                         methods=["PUT"], status_code=status.HTTP_204_NO_CONTENT)
        ra.add_api_route("/{user_id}/permissoes/{permissao}", self.remover_permissao,
                         methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT)
        self.app.include_router(ra)

    # --- administração de usuários ------------------------------------------
    def listar_usuarios(
        self, filtros: Annotated[ListarUsuariosEntrada, Query()]
    ) -> list[UsuarioSaida]:
        """Lista usuários; com `apenas_pendentes`, só os aguardando validação.

        Args:
            filtros: parâmetros de query.

        Returns:
            list[UsuarioSaida]: usuários (nunca com a senha).
        """
        with self._sessao(self._autorizacao_factory) as a:
            return [UsuarioSaida.model_validate(u) for u in a.listar_usuarios(filtros.apenas_pendentes)]

    def atualizar_usuario(
        self,
        user_id: IdUsuario,
        corpo: AtualizarUsuarioEntrada,
        ident: Annotated[Identidade, Depends(identidade_atual)],
    ) -> UsuarioSaida:
        """Valida/ativa/desativa um usuário e/ou troca o cargo.

        Args:
            user_id: usuário a alterar.
            corpo: `ativo` e/ou `cargo`.
            ident: administrador autenticado.

        Returns:
            UsuarioSaida: usuário após a alteração.

        Raises:
            HTTPException: 404 se não existir; 409 se o administrador tentar se
                desativar ou trocar o próprio cargo (evita perder o acesso).
        """
        if user_id == ident.user_id and (corpo.ativo is False or corpo.cargo is not None):
            raise HTTPException(status.HTTP_409_CONFLICT,
                                "Não é possível se desativar nem trocar o próprio cargo")
        with self._sessao(self._autorizacao_factory) as a:
            if not a.atualizar_usuario(user_id, corpo.ativo, corpo.cargo):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
            return UsuarioSaida.model_validate(a.obter_usuario(user_id))

    def permissoes_do_usuario(self, user_id: IdUsuario) -> PermissoesSaida:
        """Permissões efetivas de um usuário (cargo + exceções).

        Args:
            user_id: usuário consultado.

        Returns:
            PermissoesSaida: usuário e permissões em ordem alfabética.

        Raises:
            HTTPException: 404 se o usuário não existir.
        """
        with self._sessao(self._autorizacao_factory) as a:
            u = a.obter_usuario(user_id)
            if u is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
            return PermissoesSaida(usuario=UsuarioSaida.model_validate(u),
                                   permissoes=sorted(a.permissoes(u["id"], u["cargo"])))

    def definir_permissao(
        self, user_id: IdUsuario, permissao: str, corpo: PermissaoUsuarioEntrada
    ) -> None:
        """Concede ou nega uma permissão a um usuário, além do que o cargo define.

        Args:
            user_id: usuário alvo.
            permissao: nome da permissão.
            corpo: `concedida` True concede, False nega.

        Returns:
            None (status 204).

        Raises:
            HTTPException: 404 se o usuário não existir; 422 se a permissão for desconhecida.
        """
        with self._sessao(self._autorizacao_factory) as a:
            if not a.definir_permissao_usuario(user_id, permissao, corpo.concedida):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")

    def remover_permissao(self, user_id: IdUsuario, permissao: str) -> None:
        """Remove a exceção do usuário (volta a valer o cargo).

        Args:
            user_id: usuário alvo.
            permissao: nome da permissão.

        Returns:
            None (status 204).

        Raises:
            HTTPException: 404 se não havia exceção; 422 se a permissão for desconhecida.
        """
        with self._sessao(self._autorizacao_factory) as a:
            if not a.remover_permissao_usuario(user_id, permissao):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Exceção de permissão não encontrada")

    def login(self, corpo: LoginEntrada) -> LoginSaida:
        """Troca nome e senha por uma chave de API (rota pública).

        Args:
            corpo: nome e senha do usuário.

        Returns:
            LoginSaida: chave a enviar em `X-API-Key` e seu vencimento (UTC).

        Raises:
            HTTPException: 401 se usuário ou senha estiverem incorretos.
        """
        with self._sessao(self._autenticacao_factory) as f:
            emitida = f.login(corpo.nome, corpo.senha)
        if emitida is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário ou senha inválidos")
        return LoginSaida(chave=emitida[0], expira_em=emitida[1])

    def registrar_usuario(self, corpo: RegistroEntrada) -> RegistroSaida:
        """Registra um usuário novo, inativo até alguém validar o registro (rota pública).

        Args:
            corpo: nome e senha do novo usuário.

        Returns:
            RegistroSaida: nome criado, com `ativo` False (status 201).

        Raises:
            HTTPException: 409 se o nome já estiver em uso.
        """
        with self._sessao(self._autenticacao_factory) as f:
            novo_id = f.registrar(corpo.nome, corpo.senha)
        if novo_id is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Nome de usuário já em uso")
        return RegistroSaida(nome=corpo.nome, ativo=False)

    def health(self) -> HealthSaida:
        """Verifica a saúde da API e a existência das tabelas `pedido` e `item_pedido`.

        Returns:
            HealthSaida: status "ok" e mapa tabela -> existe.
        """
        with self._db_factory() as db:
            return HealthSaida(
                status="ok",
                tabelas={t: db.table_exists(t) for t in ("pedido", "item_pedido")},
            )

    def listar_pedidos(
        self,
        filtros: Annotated[ListarPedidosEntrada, Query()],
        ident: Annotated[Identidade, Depends(identidade_atual)],
    ) -> ListarPedidosSaida:
        """Lista pedidos com filtros opcionais e paginação.

        Args:
            filtros: parâmetros de query (obra, status_atual, limit, offset).
            ident: usuário autenticado (não admin vê só os próprios pedidos).

        Returns:
            ListarPedidosSaida: lista de pedidos (sem itens).
        """
        with self._facede() as f:
            pedidos = f.listar(
                filtros.obra,
                filtros.status_atual,
                filtros.limit,
                filtros.offset,
                None if self._admin(ident) else ident.user_id,
            )
            return [PedidoSaida.model_validate(p) for p in pedidos]

    def valores_filtros(self) -> ValoresFiltrosSaida:
        """Obras, status e origens existentes, para montar os filtros das telas.

        Returns:
            ValoresFiltrosSaida: valores distintos de obras, status e origens.
        """
        with self._sessao(self._metricas_factory) as f:
            return ValoresFiltrosSaida(**f.valores_filtros())

    def tarefas_da_obra(
        self, filtros: Annotated[TarefasEntrada, Query()]
    ) -> TarefasSaida:
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
            top = f.top_itens(
                filtros.obra,
                filtros.tarefa,
                filtros.status_atual,
                filtros.origem,
                desde,
                ate,
                filtros.limite,
            )
            return [ItemTopSaida(produto=p, quantidade=q) for p, q in top]

    def criar_pedido(
        self,
        corpo: CriarPedidoEntrada,
        response: Response,
        ident: Annotated[Identidade, Depends(identidade_atual)],
    ) -> CriarPedidoSaida:
        """Cria um pedido e define o cabeçalho `Location` com a sua URL.

        Args:
            corpo: dados do pedido a criar.
            response: resposta HTTP, onde o cabeçalho `Location` é gravado.
            ident: usuário autenticado, que passa a ser o dono do pedido.

        Returns:
            CriarPedidoSaida: pedido criado (status 201).

        Raises:
            HTTPException: 409/422 por conflito de integridade ou validação.
        """
        with self._facede() as f:
            novo = corpo.para_entidade()
            novo.user_id = ident.user_id
            pedido = f.salvar(novo)
            response.headers["Location"] = f"/pedidos/{pedido.id}"
            return PedidoSaida.model_validate(pedido)

    def obter_pedido(
        self,
        pedido_id: IdPedido,
        ident: Annotated[Identidade, Depends(identidade_atual)],
    ) -> ObterPedidoSaida:
        """Obtém um pedido com seus itens.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            ObterPedidoSaida: pedido encontrado.

        Raises:
            HTTPException: 404 se não existir.
        """
        with self._facede() as f:
            return PedidoSaida.model_validate(self._obter_ou_404(f, pedido_id, ident))

    def atualizar_pedido(
        self,
        pedido_id: IdPedido,
        corpo: AtualizarPedidoEntrada,
        ident: Annotated[Identidade, Depends(identidade_atual)],
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
            pedido = self._obter_ou_404(f, pedido_id, ident, com_itens=False)
            # Reconstrói a entidade para que as regras de validação sejam reaplicadas.
            atual = {k: v for k, v in asdict(pedido).items() if k != "itens"}
            salvo = f.salvar(Pedido(**{**atual, **corpo.campos()}))
            return PedidoSaida.model_validate(salvo)

    def remover_pedido(
        self,
        pedido_id: IdPedido,
        ident: Annotated[Identidade, Depends(identidade_atual)],
    ) -> None:
        """Remove um pedido e seus itens.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            None (status 204).

        Raises:
            HTTPException: 404 se o pedido não existir.
        """
        with self._facede() as f:
            self._obter_ou_404(f, pedido_id, ident, com_itens=False)  # só o dono (ou admin)
            if not f.remover(pedido_id):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido não encontrado")

    def listar_itens(
        self,
        pedido_id: IdPedido,
        ident: Annotated[Identidade, Depends(identidade_atual)],
    ) -> ListarItensSaida:
        """Lista os itens de um pedido.

        Args:
            pedido_id: identificador do pedido.

        Returns:
            ListarItensSaida: itens do pedido.

        Raises:
            HTTPException: 404 se o pedido não existir.
        """
        with self._facede() as f:
            self._obter_ou_404(f, pedido_id, ident, com_itens=False)
            return [
                ItemPedidoSaida.model_validate(i) for i in f.itens_do_pedido(pedido_id)
            ]

    def adicionar_item(
        self,
        pedido_id: IdPedido,
        corpo: AdicionarItemEntrada,
        ident: Annotated[Identidade, Depends(identidade_atual)],
    ) -> AdicionarItemSaida:
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
            pedido = self._obter_ou_404(f, pedido_id, ident)
            corpo.verificar(pedido)  # integridade: limite de itens e duplicidade
            pedido.itens = [corpo.para_entidade()]  # só o item novo é inserido
            pedido.num_itens += 1
            f.salvar(pedido)
            return PedidoSaida.model_validate(self._obter_ou_404(f, pedido_id, ident))

    # --- execução ------------------------------------------------------------
    @staticmethod
    def run(
        host: str = "127.0.0.1", port: int = 8000, reload: bool | None = None
    ) -> None:
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
