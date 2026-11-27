Leitura do catálogo de produtos (tabela `produtos`), paginada e com filtros. Somente leitura. Consome o [[Adapter do banco de dados]]. Implementa `facedeProdutoInterface`.

```python
with DIC.db() as db:
    f = FacedeProduto(db)
    pagina = f.listar(busca="cabo", limit=30, offset=0)
    total = f.contar(busca="cabo")
```

## funções

### \_filtro(busca: str | None, categoria: str | None) -> tuple\[str, list\]

Função interna (estática). Monta o `WHERE` comum a `listar` e `contar`:

- `categoria` → igualdade exata;
- `busca` → `LIKE` no código **ou** na descrição. Os caracteres `%`, `_` e `\` são escapados, então valem como texto comum.

### listar(self, busca=None, categoria=None, limit=100, offset=0) -> list\[dict\]

Uma página de produtos ordenada por categoria, código e id. Cada item traz `id`, `codigo`, `descricao` e `categoria`.

### contar(self, busca=None, categoria=None) -> int

Total de produtos que casam com o filtro. Use com `listar` para calcular o número de páginas.

### categorias(self) -> list\[str\]

Categorias distintas do catálogo em ordem alfabética, sem valores nulos ou vazios. Usado para montar o filtro de categoria.
