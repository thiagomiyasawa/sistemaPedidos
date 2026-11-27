O cliente é a aplicação desktop (PySide6/Qt) do sistema. Ela **não acessa o banco**: tudo passa pela API HTTP do [[API Gateway]] usando `httpx`. Código em `src/client/`.

## Como executar

- **Cliente e servidor juntos:** `python src/iniciar.py` (`monitorkpi-tudo`). Sobe o servidor (`uvicorn bancoDadosSQL.APIGateway:app`, porta 8000) em subprocesso, espera ele responder, abre o cliente e, ao fechar a janela, encerra o servidor.
- **Só o cliente:** `python src/client/paginas/sistemaLogin/paginaLogin.py` (precisa do servidor no ar).
- Cada página também roda sozinha pelo seu `main()`. Nesse caso não há login, então a chave tem que estar em `MONITORKPI_API_KEY`.

## Variáveis de ambiente

| Variável | Para quê | Padrão |
|---|---|---|
| `MONITORKPI_API_URL` | URL base da API | `http://127.0.0.1:8000` |
| `MONITORKPI_API_KEY` | chave de API inicial (uso sem login) | nenhuma |
| `MONITORKPI_SESSAO_ARQUIVO` | arquivo onde a sessão é guardada | `sessao.json` na raiz do projeto |

## Arquitetura em camadas

```
Páginas (Qt)  ──▶  Facedes (`client/facedes`)  ──▶  Adapter API  ──HTTP──▶  API Gateway
     │                    │
     └── Carrinho (estado compartilhado, com sinais Qt)
```

1. **Páginas** só conhecem facedes e entidades, nunca HTTP.
2. **Facedes** conhecem os endpoints, validam com os formulários e convertem JSON em entidades.
3. **[[Adapter da API]]** é o transporte HTTP genérico, sem regra de negócio. Os erros viram `ApiError`.

Cada camada tem uma interface (`Protocol`), então dá para trocar a implementação (por exemplo, facades de teste ligados direto ao SQLite) sem mexer em quem usa.

## Injeção de dependências (`client/DIC.py`)

Container `dependency_injector`, todos os providers são **Singleton**: uma única conexão HTTP para todo o app.

| Provider | Classe | Observação |
|---|---|---|
| `api` | `AdapterAPI` | compartilhado por todos os facedes |
| `facede_autenticacao` | `FacedeAutenticacaoAPI` | o login grava a chave em `api` e todos passam a enviá-la |
| `facede_pedido` | `FacedePedidoAPI` | |
| `facede_metricas` | `FacedeMetricasAPI` | |
| `facede_produto` | `FacedeProdutoAPI` | |
| `facede_carrinho` | `FacedeCarrinhoAPI` | |
| `carrinho` | `Carrinho` | estado local do carrinho, usa `facede_carrinho` |

Para testar sem API: `DIC.facede_pedido.override(...)` com `FacedePedidoTeste` ou `FacedeMetricasTeste` (em `facedes/objetosTeste/`), que herdam os facedes do servidor e falam direto com o SQLite.

## Notas do cliente

- [[Adapter da API]]: transporte HTTP e `ApiError`.
- [[Autenticação e sessão]]: login, sessão guardada em arquivo e restauração.
- [[Facedes de acesso ao servidor]]: pedidos, métricas, produtos e carrinho.
- [[Páginas]]: telas, fluxo de navegação e componentes.

## Entidades

- `Pedido` e `ItemPedido` (reutiliza `bancoDadosSQL.entidades.pedidos`): validam as próprias regras.
- `Produto` (`sisPedidos/entidades/produto.py`): `id`, `codigo`, `descricao`, `categoria`; imutável.
- `ItemCarrinho` (`itemCarrinho.py`): `produto`, `quant`, `uni`, `data_necessidade`, `id` (id da linha, usado para remover).
- `UNIDADES` (`unidade.py`): unidades sugeridas (un, par, cx, pç, rolo, saco, barra, m, m², m³, kg, l); o campo aceita texto livre até 20 caracteres, o mesmo limite da API.
