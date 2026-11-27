Abstrai o acesso ao banco de dados: o resto do sistema só conhece o contrato `dbAdapterInterface` (um `Protocol`, sem herança obrigatória), então dá para trocar o banco sem afetar os facedes. Implementação atual: `SQLiteAdapter` (ver [[Banco de Dados]]).

Todos os facedes ([[Facede pedido]], [[Facede carrinho]], [[Facede produto]], [[Facede metricas]], [[Facede autenticacao]], [[Facede autorizacao]]) consomem este adapter.

```python
with SQLiteAdapter() as db:
    db.execute("INSERT INTO kpi (nome) VALUES (?)", ("vendas",))
    db.execute("SELECT * FROM kpi")
    linhas = db.fetch_all()
```

## Como funciona

- **Consulta em dois passos:** `execute` guarda o cursor dentro do adapter e `fetch_all`, `fetch_one` e `fetch_batches` leem desse cursor. Um novo `execute` troca o cursor, então leia o resultado antes de executar outra coisa.
- **Linhas são dicionários** (`coluna → valor`).
- **Parâmetros** são sequência (`?`) ou dict (`:nome`). Nunca monte SQL concatenando valores do usuário.
- **Toda escrita é transacional**: `execute`, `execute_many`, `execute_script` e `insert` rodam dentro de `transaction()`.
- A conexão é aberta sob demanda e usa `row_factory` de linhas nomeadas e chaves estrangeiras ligadas. O `timeout` (padrão 30 s) é a espera por bloqueio do banco.

## Conexão

### connect(self) -> Any

Abre a conexão (ou reutiliza a já aberta), guarda no adapter e a devolve.

### close(self) -> None

Fecha a conexão, se aberta, e descarta o cursor guardado.

### \_\_enter\_\_(self) -> Self

Entrada do `with`: abre a conexão e devolve o próprio adapter.

### \_\_exit\_\_(self, exc_type, exc, tb) -> None

Saída do `with`: fecha a conexão. Não suprime exceções.

## Transações

### transaction(self) -> AbstractContextManager\[Any\]

Região de transação usada com `with`: tudo é executado ou nada é. Commit ao sair normalmente, rollback se houver exceção (que é repropagada).

Chamadas **aninhadas participam da transação mais externa**, que decide o commit ou rollback. Por isso um facede pode chamar outro na mesma conexão (ex.: `FacedeCarrinho.finalizar` usa `FacedePedido.salvar`) e tudo continua atômico.

Se um bloco interno falhar e a exceção for suprimida, a transação inteira é revertida e lança `RuntimeError`.

## Escrita

### execute(self, sql: str, params: Params = ()) -> int

Executa um comando em transação, guarda o cursor e devolve o número de linhas afetadas (`-1` em consultas).

### execute_many(self, sql: str, params_seq: Sequence\[Params\]) -> int

Executa o mesmo comando para vários conjuntos de parâmetros, em uma transação. Devolve o número de linhas afetadas.

### execute_script(self, script: str) -> None

Executa um script com vários comandos separados por `;`. Não devolve nada.

### insert(self, tabela: str, dados: dict\[str, Any\]) -> int

Insere um registro (`coluna → valor`) e devolve o id gerado. O nome da tabela é interpolado no SQL, então só pode vir do código, nunca do usuário.

## Leitura

Exigem um `execute` anterior; sem ele lançam `RuntimeError`.

### fetch_all(self) -> list\[Linha\]

Devolve todas as linhas do resultado (lista vazia se nenhuma).

### fetch_one(self) -> Linha | None

Devolve a próxima linha do resultado, ou `None` se acabou.

### fetch_batches(self, tamanho_lote: int = 1000) -> Generator\[list\[Linha\]\]

Devolve o resultado em lotes de até `tamanho_lote` linhas, sem carregar tudo na memória. Lança `ValueError` se `tamanho_lote < 1`. Ao terminar, o cursor é fechado, então depois dele não se lê mais esse resultado.

## Metadados

### table_exists(self, tabela: str) -> bool

Diz se a tabela existe no banco. Atenção: usa `execute`, então substitui o cursor guardado.
