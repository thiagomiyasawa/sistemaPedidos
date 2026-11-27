Consultas agregadas sobre pedidos e itens. **Só lê**; escrita e CRUD ficam no [[Facede pedido]]. Consome o [[Adapter do banco de dados]]. Implementa `facedeMetricasInterface`.

```python
with DIC.db() as db:
    top = FacedeMetricas(db).top_itens(obra="A", limite=5)
```

As datas (`data_criacao`) são texto `YYYY-MM-DD HH:MM:SS` em UTC, então a comparação de texto equivale à cronológica.

## funções

### \_filtro_pedidos(obra, tarefa, status_atual, origem, desde, ate) -> tuple\[str, list\]

Função interna (estática). Monta o `WHERE` sobre `pedido` (apelido `p`). `desde` é inclusivo e `ate` é exclusivo. Lança `ValueError` se `tarefa` vier sem `obra` (a tarefa só tem sentido dentro de uma obra).

### \_distintos(self, coluna, onde="", params=()) -> list\[str\]

Função interna. Valores distintos de uma coluna de `pedido`, em ordem alfabética. Como o nome da coluna entra no SQL, só são aceitas `obra`, `tarefa`, `status_atual` e `origem`; qualquer outra lança `ValueError`.

### valores_filtros(self) -> dict\[str, list\[str\]\]

Valores usados nos pedidos para montar filtros: `obras`, `status` e `origens`.

### tarefas_da_obra(self, obra: str) -> list\[str\]

Tarefas distintas dos pedidos de uma obra. Lança `ValueError` se `obra` for vazia.

### top_itens(self, obra=None, tarefa=None, status_atual=None, origem=None, desde=None, ate=None, limite=10) -> list\[tuple\[str, int\]\]

Produtos mais pedidos: soma `quant` dos itens dos pedidos que passam nos filtros. Retorna pares `(produto, total)` do maior para o menor; empate é resolvido por ordem alfabética do produto.
