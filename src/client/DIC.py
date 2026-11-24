"""Container de injeção de dependências do cliente (interface gráfica).

`DIC.facede_pedido()` devolve o facade de pedidos sobre a API HTTP; é um singleton,
compartilhado por toda a interface (uma única conexão HTTP reutilizada).

Para usar o banco direto (testes, sem subir a API), troque o provider:
    DIC.facede_pedido.override(DIC.facede_pedido_teste)
"""

from dependency_injector import containers, providers

from client.adapters.adapterAPI import AdapterAPI
from client.facedes.facedeAutenticacao import FacedeAutenticacaoAPI
from client.paginas.sisPedidos.acessoServidor.facedeCarrinho import FacedeCarrinhoAPI
from client.paginas.sisPedidos.acessoServidor.facedeProduto import FacedeProdutoAPI
from client.paginas.sisPedidos.carrinho import Carrinho
from client.paginas.monitorkpi.acessoServidor.facedeMetricas import FacedeMetricasAPI  # noqa: F401  (alternativa à API)
from client.paginas.monitorkpi.acessoServidor.facedePedido import FacedePedidoAPI
from client.paginas.monitorkpi.objetosTeste.facedeMetricasTeste import (
    FacedeMetricasTeste,
)
from client.paginas.monitorkpi.objetosTeste.facedePedidoTeste import FacedePedidoTeste


class DIC(containers.DeclarativeContainer):
    """Container de injeção de dependências da interface gráfica.

    Atributos:
        facede_pedido: provider singleton do facade de pedidos (atualmente
            `FacedePedidoTeste`, ligado direto ao SQLite; a alternativa via API
            está comentada).
        facede_metricas: provider singleton do facade de métricas (atualmente
            `FacedeMetricasTeste`; a alternativa via API está comentada).
    """

    api = providers.Singleton(AdapterAPI)
    # Compartilha o adapter: o login grava a chave nele e os demais facades a passam a usar.
    facede_autenticacao = providers.Singleton(FacedeAutenticacaoAPI, api=api)
    facede_pedido = providers.Singleton(FacedePedidoAPI, api=api)

    # Alternativa para testes: liga direto ao SQLite, sem a API.
    # facede_pedido = providers.Singleton(FacedePedidoTeste)

    # Métricas (consultas agregadas): mesma ideia, com a alternativa pela API comentada.
    facede_metricas = providers.Singleton(FacedeMetricasAPI, api=api)

    # Catálogo de produtos (página de catálogo).
    facede_produto = providers.Singleton(FacedeProdutoAPI, api=api)

    # Carrinho do usuário (guardado no banco, via API).
    facede_carrinho = providers.Singleton(FacedeCarrinhoAPI, api=api)

    # Carrinho compartilhado: o catálogo adiciona e a página do carrinho exibe.
    carrinho = providers.Singleton(Carrinho, facede=facede_carrinho)
    # facede_metricas = providers.Singleton(FacedeMetricasTeste)
