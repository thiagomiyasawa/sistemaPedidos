"""Container de injeção de dependências do acesso ao banco de dados."""
from dependency_injector import containers, providers

from .facedes.facedeAutenticacao import FacedeAutenticacao
from .facedes.facedeAutorizacao import FacedeAutorizacao
from .facedes.facedeMetricas import FacedeMetricas
from .facedes.facedePedido import FacedePedido
from .SQLite.SQLiteAdapter import SQLiteAdapter


class DIC(containers.DeclarativeContainer):
    """Container declarativo de injeção de dependências.

    Responsabilidade: montar o adapter de banco e os facades que dependem dele.

    Attributes:
        db: fábrica de `SQLiteAdapter` (nova instância/conexão a cada chamada).
        facede_pedido: fábrica de `FacedePedido` com `db` injetado.
        facede_metricas: fábrica de `FacedeMetricas` com `db` injetado.
    """

    # Cada chamada de `DIC.db()` devolve uma nova instância (e conexão) do adapter,
    # que satisfaz `dbAdapterInterface`.
    db = providers.Factory(SQLiteAdapter)

    # `DIC.facede_pedido()` devolve um FacedePedido já com um adapter novo injetado.
    # O dono do facade deve fechar a conexão: `facede.db.close()`.
    facede_pedido = providers.Factory(FacedePedido, db=db)

    # `DIC.facede_metricas()`: idem, para as consultas agregadas (rankings, somas).
    facede_metricas = providers.Factory(FacedeMetricas, db=db)

    # `DIC.facede_autenticacao()`: valida chaves de API na tabela `chavesAPI`; idem facades acima.
    facede_autenticacao = providers.Factory(FacedeAutenticacao, db=db)

    # `DIC.facede_autorizacao()`: permissões por cargo/usuário e administração de usuários.
    facede_autorizacao = providers.Factory(FacedeAutorizacao, db=db)
