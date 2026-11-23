"""Container de injeção de dependências do cliente (interface gráfica).

`DIC.facede_pedido()` devolve o facade de pedidos sobre a API HTTP; é um singleton,
compartilhado por toda a interface (uma única conexão HTTP reutilizada).

Para usar o banco direto (testes, sem subir a API), troque o provider:
    DIC.facede_pedido.override(DIC.facede_pedido_teste)
"""
from dependency_injector import containers, providers

from monitorkpi.acessoServidor.adapterAPI import AdapterAPI
from monitorkpi.acessoServidor.facedeMetricas import FacedeMetricasAPI  # noqa: F401  (alternativa à API)
from monitorkpi.acessoServidor.facedePedido import FacedePedidoAPI
from monitorkpi.objetosTeste.facedeMetricasTeste import FacedeMetricasTeste
from monitorkpi.objetosTeste.facedePedidoTeste import FacedePedidoTeste


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
    facede_pedido = providers.Singleton(FacedePedidoAPI, api=api)

    # Alternativa para testes: liga direto ao SQLite, sem a API.
    #facede_pedido = providers.Singleton(FacedePedidoTeste)

    # Métricas (consultas agregadas): mesma ideia, com a alternativa pela API comentada.
    facede_metricas = providers.Singleton(FacedeMetricasAPI, api=api)
    #facede_metricas = providers.Singleton(FacedeMetricasTeste)
