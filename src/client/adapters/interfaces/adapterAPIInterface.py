"""Interface (contrato) do adapter de acesso à API de pedidos.

Qualquer implementação (HTTP real, fake para testes, ...) deve satisfazer
`adapterAPIInterface`. Por ser um `Protocol`, não é preciso herdar dela.
Todas as falhas devem ser sinalizadas com `ApiError`.
"""
from __future__ import annotations

from typing import Any, Protocol, Self, runtime_checkable

Json = dict[str, Any]


class ApiError(Exception):
    """Falha ao falar com a API (rede, timeout ou resposta de erro)."""

    def __init__(self, mensagem: str, status_code: int | None = None, detalhe: Any = None) -> None:
        """Cria o erro da API.

        Args:
            mensagem: texto descritivo do erro.
            status_code: código HTTP da resposta, ou None se não houve resposta.
            detalhe: conteúdo de `detail` devolvido pela API (ou texto da resposta), ou None.
        """
        super().__init__(mensagem)
        self.status_code = status_code
        self.detalhe = detalhe


@runtime_checkable
class adapterAPIInterface(Protocol):
    """Contrato do transporte HTTP (sem endpoints de negócio, que ficam no facade).

    Uso:
        with MeuAdapter() as api:
            pedidos = api.get("/pedidos", obra="Subestação Alfa")
    """

    # --- ciclo de vida -----------------------------------------------------
    def close(self) -> None:
        """Libera a conexão/recursos.

        Returns:
            None.
        """
        ...

    def __enter__(self) -> Self:
        """Entra no contexto `with`.

        Returns:
            O próprio adapter.
        """
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o adapter.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None.
        """
        ...

    def definir_api_key(self, chave: str) -> None:
        """Passa a enviar `chave` no cabeçalho `X-API-Key` nas próximas requisições.

        Args:
            chave: chave de API obtida no login.

        Returns:
            None.
        """
        ...

    # --- requisição genérica ----------------------------------------------
    def request(self, metodo: str, caminho: str, *, params: dict | None = None,
                json: Any = None) -> Any:
        """Envia a requisição e devolve o JSON da resposta (None se sem corpo).

        Levanta `ApiError` em falha de rede, timeout ou resposta de erro.
        """
        ...

    def get(self, caminho: str, **params: Any) -> Any:
        """Faz uma requisição GET.

        Args:
            caminho: caminho do endpoint.
            **params: parâmetros de query (valores None são ignorados).

        Returns:
            JSON da resposta, ou None se sem corpo.

        Raises:
            ApiError: em falha de rede, timeout ou resposta de erro.
        """
        ...

    def post(self, caminho: str, json: Any = None) -> Any:
        """Faz uma requisição POST.

        Args:
            caminho: caminho do endpoint.
            json: corpo JSON a enviar, ou None.

        Returns:
            JSON da resposta, ou None se sem corpo.

        Raises:
            ApiError: em falha de rede, timeout ou resposta de erro.
        """
        ...

    def patch(self, caminho: str, json: Any = None) -> Any:
        """Faz uma requisição PATCH.

        Args:
            caminho: caminho do endpoint.
            json: corpo JSON com as alterações, ou None.

        Returns:
            JSON da resposta, ou None se sem corpo.

        Raises:
            ApiError: em falha de rede, timeout ou resposta de erro.
        """
        ...

    def delete(self, caminho: str) -> None:
        """Faz uma requisição DELETE.

        Args:
            caminho: caminho do recurso a remover.

        Returns:
            None.

        Raises:
            ApiError: em falha de rede, timeout ou resposta de erro.
        """
        ...
