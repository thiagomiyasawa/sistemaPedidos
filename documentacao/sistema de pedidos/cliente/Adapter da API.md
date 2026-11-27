Transporte HTTP do [[Cliente]] (`client/adapters/adapterAPI.py`, contrato em `interfaces/adapterAPIInterface.py`). Genérico: **não conhece endpoints de negócio**, que ficam nos [[Facedes de acesso ao servidor|facedes]]. Fala com o [[API Gateway]].

```python
with AdapterAPI() as api:
    pedidos = api.get("/pedidos", obra="Subestação Alfa", limit=50)
    api.patch("/pedidos/1", json={"status_atual": "entregue"})
```

## ApiError

Toda falha vira `ApiError(mensagem, status_code, detalhe)`:

- `status_code`: código HTTP, ou `None` se não houve resposta (rede, timeout).
- `detalhe`: conteúdo de `detail` da resposta (ou o texto dela).

| Situação | Mensagem | `status_code` |
|---|---|---|
| Timeout | `Tempo esgotado ao acessar <url>` | None |
| Falha de conexão | `Falha de conexão com <url>: ...` | None |
| Resposta de erro | `HTTP <código> em <método> <caminho>: <detalhe>` | o código |

Quem chama decide o que fazer com cada código: os facedes tratam 404 como "não existe" e o login trata 401 como "credenciais inválidas".

## AdapterAPI

### \_\_init__(base_url=None, timeout=10.0, api_key=None)

URL base: argumento, senão `MONITORKPI_API_URL`, senão `http://127.0.0.1:8000`. A chave: argumento, senão `MONITORKPI_API_KEY`; sem chave, nenhum cabeçalho é enviado. Cria um `httpx.Client` reaproveitado entre as requisições.

### definir_api_key(chave: str) -> None

Passa a enviar `chave` em `X-API-Key` nas próximas requisições; chave vazia remove o cabeçalho. É assim que o login "liga" todos os facedes que compartilham o adapter.

### request(metodo, caminho, *, params=None, json=None) -> Any

Envia e devolve o JSON da resposta (`None` se 204 ou sem corpo). Parâmetros de query com valor `None` são descartados.

### get(caminho, **params) / post(caminho, json=None) / patch(caminho, json=None) / delete(caminho)

Atalhos de `request`. `delete` devolve `None` e lança `ApiError` também no 404.

### get_pagina(caminho, **params) -> tuple[Any, int]

GET de lista paginada: devolve `(página, total)`. O total vem do cabeçalho `X-Total-Count` do servidor; se faltar, usa o tamanho da página.

### close() e with

`close()` fecha o cliente HTTP. O adapter funciona como context manager.
