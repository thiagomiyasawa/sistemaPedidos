Porta de entrada HTTP do servidor (FastAPI). A classe `APIGateway` recebe as requisições, autentica e autoriza o usuário, valida entrada e saída com os formulários de `formulariosAPI`, converte para as entidades `Pedido`/`ItemPedido` e delega a persistência aos facedes, que chegam por injeção de dependência (`DIC`).

```
Cliente ──HTTP──▶ APIGateway ──▶ Facedes ──▶ Adapter do banco ──▶ Banco de dados
                    │
                    ├─ autentica: Facede autenticação
                    ├─ autoriza:  Facede autorização
                    └─ dados:     Facede pedido · carrinho · produto · métricas
```

Links: [[Facede autenticacao]], [[Facede autorizacao]], [[Facede pedido]], [[Facede carrinho]], [[Facede produto]], [[Facede metricas]], [[Adapter do banco de dados]], [[Banco de Dados]].

## Executar

- `python src/bancoDadosSQL/APIGateway.py` (ou `APIGateway.run()`); também por `uvicorn bancoDadosSQL.APIGateway:app`.
- **Modo dev** (padrão): Swagger em `/docs`, ReDoc em `/redoc`, esquema em `/openapi.json` e `reload` ligado.
- **Produção**: defina `MONITORKPI_ENV=producao` (ou `dev=False`) para desligar a documentação e o reload.
- Padrão: `127.0.0.1:8000`.

## Injeção de dependências

O construtor recebe **fábricas** (não instâncias) para cada facade, com os padrões do `DIC`: `facede_factory`, `db_factory`, `metricas_factory`, `autenticacao_factory`, `autorizacao_factory`, `produto_factory` e `carrinho_factory`. Cada requisição cria o seu facade e, portanto, a sua conexão, porque a conexão SQLite é presa à thread do endpoint. Para testar, passe fábricas de facades falsos.

## Autenticação

- Toda rota exige o cabeçalho **`X-API-Key`** com uma chave válida (existente, não vencida e de usuário ativo). Isso vale até para `/health`.
- Exceções, em `ROTAS_PUBLICAS`: **`/login`** e **`/registro`**, por onde a chave é obtida.
- A verificação é uma dependência **global** (`_autenticar`), então roda em todas as rotas, inclusive as futuras. Ela busca a identidade, carrega as permissões efetivas do usuário e guarda tudo em `request.state`.
- Falha → **401** com `WWW-Authenticate: ApiKey`.

Fluxo típico: `POST /registro` → um administrador ativa o usuário (`PATCH /admin/usuarios/{id}`) → `POST /login` devolve a chave → as demais chamadas enviam `X-API-Key`.

## Autorização

`exige(tabela, acao, todos=False)` cria a dependência de cada rota e responde **403** se faltar permissão:

- a identidade precisa ter a ação (`criar`, `atualizar`, `deletar` ou `ler`) na tabela;
- com `todos=True`, precisa também da flag `todos`, usada nas rotas que agregam dados de todos os usuários.

**Dono do pedido:** quem não tem `todos` em `pedido` só vê e altera os **próprios** pedidos. Pedido de outro usuário devolve **404** (não 403), para não revelar que o id existe.

## Erros

`_sessao` entrega o facade, traduz erros de domínio e sempre fecha a conexão ao sair:

| Erro | HTTP |
|---|---|
| `ConflitoIntegridade` (formulário) | 409 |
| `sqlite3.IntegrityError` | 409 |
| `ValueError` (regra de validação) | 422 |
| Chave inválida, vencida ou ausente | 401 |
| Sem permissão | 403 |
| Recurso inexistente (ou de outro usuário) | 404 |

## Rotas

Coluna **Permissão**: `tabela.ação`; "+todos" exige também a flag `todos`.

### infra e auth

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/health` | só chave | Status e se `pedido` e `item_pedido` existem |
| POST | `/login` | pública | Nome e senha → chave e vencimento (UTC). Reaproveita a chave vigente; 401 se credencial inválida ou usuário inativo |
| POST | `/logout` | só chave | Revoga a chave (204). Encerra a sessão em todos os dispositivos que a compartilham |
| POST | `/registro` | pública | Cria usuário **inativo** (201); 409 se o nome já existe |

### pedidos

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/pedidos` | pedido.ler | Lista pedidos (sem itens). Query: `obra`, `status_atual`, `ordem`, `apenas_meus`, `limit`, `offset`. Total no cabeçalho `X-Total-Count` |
| GET | `/pedidos/status` | pedido.ler | Status distintos visíveis ao usuário (`apenas_meus`) |
| POST | `/pedidos` | pedido.criar | Cria pedido (201) com o usuário como dono; cabeçalho `Location: /pedidos/{id}` |
| GET | `/pedidos/{id}` | pedido.ler | Pedido com itens |
| PATCH | `/pedidos/{id}` | pedido.atualizar | Atualização parcial; as regras da entidade são revalidadas |
| DELETE | `/pedidos/{id}` | pedido.deletar | Remove pedido e itens (204) |
| GET | `/pedidos/{id}/itens` | item_pedido.ler | Itens do pedido |
| POST | `/pedidos/{id}/itens` | item_pedido.criar | Adiciona item (201); 409 se passar do limite de itens ou duplicar |

`/pedidos/status` é registrada antes de `/pedidos/{id}`, senão "status" seria lido como id.

### catálogo

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/produtos` | pedido.ler | Página do catálogo. Query: `busca`, `categoria`, `limit`, `offset`. Total em `X-Total-Count` |
| GET | `/produtos/categorias` | pedido.ler | Categorias distintas |

Não há permissão própria para produtos; lê quem pode ler pedidos.

### carrinho

Sempre o carrinho **do usuário autenticado**. Exige `pedido.ler` em todas as rotas.

| Método | Rota | Permissão extra | Descrição |
|---|---|---|---|
| GET | `/carrinho` | — | Itens do carrinho |
| DELETE | `/carrinho` | — | Esvazia (204) |
| POST | `/carrinho/itens` | — | Soma um produto (201) e devolve o carrinho; 404 se o produto não existe |
| DELETE | `/carrinho/itens/{item_id}` | — | Remove uma linha (204); 404 se não for do usuário |
| POST | `/carrinho/finalizar` | pedido.criar | Cria o pedido com o carrinho e o esvazia (201); 422 se vazio |

### métricas e filtros

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/itens/top` | pedido.ler +todos | Produtos mais pedidos. Query: `obra`, `tarefa`, `status_atual`, `origem`, período, `limite`. Tarefa exige obra (422) |
| GET | `/filtros` | pedido.ler +todos | Obras, status e origens existentes |
| GET | `/filtros/tarefas` | pedido.ler +todos | Tarefas de uma obra (`obra` obrigatória) |

### admin

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| GET | `/admin/usuarios` | usuario.ler +todos | Lista usuários; `apenas_pendentes` mostra os aguardando validação |
| PATCH | `/admin/usuarios/{id}` | usuario.atualizar +todos | Ativa ou desativa e/ou troca o cargo |
| GET | `/admin/usuarios/{id}/permissoes` | usuario_permissao.ler | Permissões efetivas por tabela |
| PUT | `/admin/usuarios/{id}/permissoes/{tabela}` | usuario_permissao.atualizar | Define a permissão do usuário na tabela, no lugar da do cargo (204) |
| DELETE | `/admin/usuarios/{id}/permissoes/{tabela}` | usuario_permissao.deletar | Volta a valer a do cargo (204) |

Regra de proteção: um administrador **não pode se desativar nem trocar o próprio cargo** (409), para não perder o acesso.

## Funções de apoio

- **ambiente_dev()** → True, exceto se `MONITORKPI_ENV` for `producao`.
- **exige(tabela, acao, todos)** → dependência de autorização (ver acima).
- **identidade_atual(request)** → dependência das rotas protegidas; devolve a `Identidade` gravada pela autenticação (401 se não houver).
- **\_ve_todos(ident)** → True se a permissão efetiva em `pedido` tem `todos`.
- **\_obter_ou_404(f, pedido_id, ident, com_itens)** → busca o pedido e dá 404 se não existir ou não for do usuário (sem `todos`).
- **\_sessao(factory)** → context manager que entrega o facade, traduz erros e fecha a conexão.
