"""Adapter cliente HTTP para a API de pedidos (`bancoDadosSQL.APIGateway`).

Transporte HTTP genérico (get/post/patch/delete): não conhece endpoints de negócio,
que ficam no facade (`facedePedido`). Erros viram `ApiError`.

Uso:
    with AdapterAPI() as api:
        pedidos = api.get("/pedidos", obra="Subestação Alfa", limit=50)
        api.patch("/pedidos/1", json={"status_atual": "entregue"})

URL base: argumento `base_url`, senão variável de ambiente MONITORKPI_API_URL,
senão http://127.0.0.1:8000.
"""
from __future__ import annotations

import os
from typing import Any, Self

import httpx

from monitorkpi.acessoServidor.interfaces.adapterAPIInterface import ApiError, adapterAPIInterface

__all__ = ["AdapterAPI", "ApiError"]

URL_PADRAO = "http://127.0.0.1:8000"


class AdapterAPI(adapterAPIInterface):
    """Transporte HTTP (httpx) para a API de pedidos.

    Atributos:
        base_url: URL base da API, sem barra final.
        _client: cliente `httpx.Client` reutilizado entre as requisições.
    """

    def __init__(self, base_url: str | None = None, timeout: float = 10.0,
                 api_key: str | None = None) -> None:
        """Cria o adapter e o cliente HTTP.

        Args:
            base_url: URL base da API; se None usa a variável de ambiente
                MONITORKPI_API_URL ou `URL_PADRAO`.
            timeout: tempo limite, em segundos, de cada requisição.
            api_key: chave enviada no cabeçalho `X-API-Key`; se None usa a variável
                de ambiente MONITORKPI_API_KEY (sem chave, nenhum cabeçalho é enviado).
        """
        self.base_url = (base_url or os.environ.get("MONITORKPI_API_URL") or URL_PADRAO).rstrip("/")
        chave = api_key or os.environ.get("MONITORKPI_API_KEY")
        headers = {"X-API-Key": chave} if chave else {}
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout, headers=headers)

    # --- ciclo de vida -----------------------------------------------------
    def close(self) -> None:
        """Fecha o cliente HTTP e libera as conexões.

        Returns:
            None.
        """
        self._client.close()

    def __enter__(self) -> Self:
        """Entra no contexto `with`.

        Returns:
            O próprio adapter.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Sai do contexto `with`, fechando o adapter.

        Args:
            exc_type: tipo da exceção ocorrida no bloco, ou None.
            exc: instância da exceção, ou None.
            tb: traceback, ou None.

        Returns:
            None (exceções não são suprimidas).
        """
        self.close()

    # --- requisição genérica ----------------------------------------------
    def request(self, metodo: str, caminho: str, *, params: dict | None = None,
                json: Any = None) -> Any:
        """Envia a requisição e devolve o JSON da resposta (None se 204).

        Args:
            metodo: método HTTP (GET, POST, PATCH, DELETE).
            caminho: caminho do endpoint, relativo à URL base.
            params: parâmetros de query; valores None são descartados.
            json: corpo JSON da requisição, ou None.

        Returns:
            JSON decodificado da resposta, ou None se 204 ou sem corpo.

        Raises:
            ApiError: em timeout, falha de conexão ou resposta HTTP de erro.
        """
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        try:
            resp = self._client.request(metodo, caminho, params=params, json=json)
        except httpx.TimeoutException as e:
            raise ApiError(f"Tempo esgotado ao acessar {self.base_url}") from e
        except httpx.HTTPError as e:
            raise ApiError(f"Falha de conexão com {self.base_url}: {e}") from e

        if resp.is_error:
            try:
                detalhe = resp.json().get("detail")
            except ValueError:
                detalhe = resp.text
            raise ApiError(f"HTTP {resp.status_code} em {metodo} {caminho}: {detalhe}",
                           resp.status_code, detalhe)
        return None if resp.status_code == 204 or not resp.content else resp.json()

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
        return self.request("GET", caminho, params=params)

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
        return self.request("POST", caminho, json=json)

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
        return self.request("PATCH", caminho, json=json)

    def delete(self, caminho: str) -> None:
        """Faz uma requisição DELETE.

        Args:
            caminho: caminho do recurso a remover.

        Returns:
            None.

        Raises:
            ApiError: em falha de rede, timeout ou resposta de erro (inclusive 404).
        """
        self.request("DELETE", caminho)
