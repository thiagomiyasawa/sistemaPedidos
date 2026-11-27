Gerencia o carrinho de cada usuário (tabela `carrinho_itens_cadastro`): os produtos que ele separou antes de virar pedido. Consome o [[Adapter do banco de dados]] e, em `finalizar`, o [[Facede pedido]] (na mesma conexão). Implementa `facedeCarrinhoInterface`.

Uma linha do carrinho = **um produto numa data de necessidade e numa unidade**. A combinação `usuário + produto + data + unidade` é única; o mesmo produto pode ter várias linhas se a data ou a unidade mudarem.

```python
with DIC.db() as db:
    itens = FacedeCarrinho(db).listar(user_id=1)
```

## constantes

- `STATUS_INICIAL = "Aberto"` — status do pedido criado pelo carrinho.
- `ORIGEM_PEDIDO = "Sistema de Pedidos"` — origem do pedido criado pelo carrinho.

## funções

### listar(self, user_id: int) -> list\[dict\]

Itens do carrinho do usuário na ordem de inclusão, já com os dados do produto: `id` (da linha), `produto_id`, `codigo`, `descricao`, `categoria`, `quantidade`, `unidade` e `data_necessidade` (texto ISO).

### adicionar(self, user_id, produto_id, quantidade, unidade, data_necessidade: date) -> bool

Soma `quantidade` à linha do produto naquela data/unidade; cria a linha se não existir (um único `INSERT ... ON CONFLICT DO UPDATE`). Retorna False se o produto não existir.

Lança `ValueError` se `quantidade` não for positiva.

### remover(self, user_id: int, itens_ids: Iterable\[int\]) -> int

Remove as linhas indicadas. Ids que não existem ou são de outro usuário são ignorados (um usuário nunca apaga o carrinho de outro). Retorna quantas linhas foram removidas; lista vazia retorna 0 sem consultar o banco.

### finalizar(self, user_id, obra, tarefa, local_entrega) -> int

Transforma o carrinho em pedido, **em uma única transação**:

1. lê as linhas do carrinho (`listar`);
2. monta os `ItemPedido` (produto = `codigo - descricao`);
3. cria o `Pedido` com status `Aberto` e origem `Sistema de Pedidos` e grava com `FacedePedido.salvar` (a transação do `salvar` participa da deste bloco);
4. esvazia o carrinho (`limpar`).

Retorna o id do pedido. Lança `ValueError` se o carrinho estiver vazio ou os dados violarem as regras do pedido; nesse caso nada é criado e o carrinho fica como estava.

### limpar(self, user_id: int) -> None

Esvazia o carrinho do usuário.
