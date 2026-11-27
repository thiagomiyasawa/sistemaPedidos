Os facedes do [[Cliente]] conhecem os endpoints do [[API Gateway]], validam a entrada com formulários (os mesmos do servidor, em `client/facedes/formulariosAPI`), chamam o [[Adapter da API]] e devolvem **entidades**, não JSON. Todos aceitam `api` por injeção (padrão: um `AdapterAPI` novo), têm `close()` e funcionam com `with`.

| Facede | Arquivo | Endpoints |
|---|---|---|
| `FacedePedidoAPI` | `facedes/facedePedido.py` | `/health`, `/pedidos...` |
| `FacedeMetricasAPI` | `facedes/facedeMetricas.py` | `/filtros`, `/filtros/tarefas`, `/itens/top` |
| `FacedeProdutoAPI` | `facedes/facedeProduto.py` | `/produtos`, `/produtos/categorias` |
| `FacedeCarrinhoAPI` | `facedes/facedeCarrinho.py` | `/carrinho...` |

Todos ficam em `client/facedes/`, junto das interfaces (`interfaces/`), dos formulários (`formulariosAPI/`) e dos facedes de teste (`objetosTeste/`). As entidades que eles devolvem ficam em `client/entidades/`. O login tem facade próprio: [[Autenticação e sessão]].

Convenção: 404 vira "não existe" (`None`, `False` ou lista vazia) quando faz sentido; o resto sobe como `ApiError`.

## FacedePedidoAPI

- **health()** → JSON de `GET /health`.
- **obter(pedido_id, com_itens=True)** → `Pedido` ou `None` (404). Com `com_itens=False`, devolve sem itens.
- **listar(obra, status_atual, limit=100, offset=0, apenas_meus=False)** → `list[Pedido]` de uma página. Os filtros são validados antes de chamar a API (`ValueError`).
- **listar_todos(obra, status_atual, tamanho_pagina=1000)** → todos os pedidos do filtro, percorrendo as páginas até vir uma incompleta.
- **listar_meus_pagina(status_atual, limit=30, offset=0)** → `(pedidos, total)` só do usuário, do mais novo para o mais antigo (`ordem=desc`, `apenas_meus`); o total vem de `X-Total-Count`.
- **status_dos_meus()** → status distintos dos pedidos do usuário (`GET /pedidos/status`).
- **itens_do_pedido(pedido_id)** → `list[ItemPedido]`; lista vazia se o pedido não existe.
- **salvar(pedido)** → sem `id`: `POST /pedidos`. Com `id`: `PATCH /pedidos/{id}` e depois um `POST .../itens` para cada item sem `id`. Devolve o pedido como o servidor salvou.
- **remover(pedido_id)** → True se removeu, False se não existia (404).

## FacedeMetricasAPI

- **valores_filtros()** → `{"obras", "status", "origens"}`.
- **tarefas_da_obra(obra)** → tarefas da obra. A obra é validada antes (sem obra, nem faz a requisição).
- **top_itens(obra, tarefa, status_atual, origem, dias, de, ate, limite=10)** → `list[(produto, total)]`, do maior para o menor. O período é `dias` (últimos N dias) **ou** `de`/`ate`, não os dois.

Essas rotas exigem a flag `todos` em `pedido` (ver [[Facede autorizacao]]); sem ela o servidor responde 403.

## FacedeProdutoAPI

- **listar_pagina(busca, categoria, limit=30, offset=0)** → `(list[Produto], total)`. A busca e a paginação são feitas no servidor.
- **categorias()** → categorias do catálogo em ordem alfabética.

## FacedeCarrinhoAPI

O carrinho fica no banco, por usuário; o cliente só espelha.

- **listar()** → `list[ItemCarrinho]` na ordem de inclusão.
- **adicionar(produto_id, quant, uni, data_necessidade)** → soma ao produto naquela data e unidade (`POST /carrinho/itens`); devolve o carrinho atualizado.
- **remover(itens_ids)** → apaga as linhas uma a uma; 404 é ignorado.
- **finalizar(obra, tarefa, local_entrega)** → `POST /carrinho/finalizar`. O cliente envia só o que o carrinho não tem; o **servidor monta o pedido** com as linhas e esvazia o carrinho. Devolve o id do pedido.
- **limpar()** → `DELETE /carrinho`.

## Carrinho (estado compartilhado)

`client/paginas/sisPedidos/carrinho.py` (ver [[Carrinho (estado compartilhado)]]). Objeto único (`DIC.carrinho()`), um `QObject` que mantém uma **cópia local** (`itens: dict[id → ItemCarrinho]`) para as telas não irem à API a cada redesenho.

- Cada alteração grava **primeiro na API**; só se der certo a cópia local é trocada pelo que o servidor devolveu. Se falhar, o estado não muda e o sinal `falhou(str)` é emitido com a mensagem.
- Sinais: `alterado()` (itens mudaram) e `falhou(str)`.
- Métodos: `recarregar()`, `adicionar(produto, quant, uni, data)`, `remover(ids)` e `limpar()` devolvem `bool`. `finalizar(...)` é a exceção: a falha sobe como `ApiError`, para a tela mostrar um aviso próprio, e o carrinho local não muda.

## Facedes de teste

`facedes/objetosTeste/facedePedidoTeste.py` e `facedeMetricasTeste.py` herdam os facedes do servidor e falam **direto com o SQLite**, com a mesma interface dos facedes de API. Servem para rodar a interface sem subir o servidor.
