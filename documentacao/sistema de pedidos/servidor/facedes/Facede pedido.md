Consome a interface do [[Adapter do banco de dados]] para realizar as operações relacionadas aos pedidos (`Pedido` e `ItemPedido`). Esconde o SQL e as transações do resto do sistema. Implementa `facedePedidoInterface`.

Usado também pelo [[Facede carrinho]], em `finalizar`, para criar o pedido.

```python
with DIC.db() as db:
    facede = FacedePedido(db)
    pedido = facede.salvar(Pedido(num_itens=1, status_atual="novo", origem="RM",
                                  local_entrega="Obra A", obra="A", tarefa="T1"))
```

## funções

### obter(self, pedido_id: int, com_itens: bool = True) -> Pedido | None

Busca o pedido pelo id. Se `com_itens` for True, carrega também os itens (via `itens_do_pedido`). Retorna `None` se o pedido não existir.

### \_filtro(obra, status_atual, user_id) -> tuple\[str, list\]

Função interna (estática). Monta a cláusula `WHERE` e a lista de parâmetros a partir dos filtros informados (valores `None` ou vazios são ignorados). Compartilhada por `listar`, `contar` e `status_distintos`.

### listar(self, obra=None, status_atual=None, limit=100, offset=0, user_id=None, ordem="asc") -> list\[Pedido\]

Lista pedidos **sem itens**, com filtros e paginação (`limit`/`offset`). Ordena por id: `ordem="asc"` (padrão) ou `"desc"` (mais novo primeiro). Qualquer outro valor de `ordem` vale como `asc`.

### contar(self, obra=None, status_atual=None, user_id=None) -> int

Conta quantos pedidos casam com os filtros. Serve para calcular o número de páginas junto com `listar`.

### status_distintos(self, user_id=None) -> list\[str\]

Status distintos que existem nos pedidos (em ordem alfabética). Se `user_id` for informado, considera só os pedidos desse dono.

### itens_do_pedido(self, pedido_id: int) -> list\[ItemPedido\]

Devolve os itens do pedido (lista vazia se não houver).

### salvar(self, pedido: Pedido) -> Pedido

Grava o pedido e seus itens **em uma única transação**:

- `pedido.id` é `None` → insere; senão → atualiza.
- Itens sem `id_pedido` são inseridos; o `id` do item é o número sequencial dentro do pedido (1, 2, 3…), continuando a partir do maior já existente.
- Itens que já têm `id_pedido` não são alterados.

Retorna o pedido relido do banco, com itens. Se o banco falhar (ex.: violação de integridade), faz rollback e propaga o erro.

### remover(self, pedido_id: int) -> bool

Remove os itens e o pedido em uma transação. Retorna True se o pedido existia.
