
É um adapter para abstrair o acesso ao banco de dados, dessa forma é possivel mudar o banco sem afetar o resto do sistema.

## funções

### connect(self) -> Any

Essa função serve para fazer a conexão com o banco de dados e armazena essa conexão no adapter e retorna a conexão.

### close(self) -> None

fecha a conexão registrada no adapter

### \_\_enter\_\_(self) -> Self

Essa função define o comportamento de entrada do objeto adapter quando for usado dentro de um with

### \_\_exit\_\_(self, exc_type, exc, tb) -> None

Essa função define o comportamento de saida do objeto adapter quando for usado dentro de um with


### transaction(self) -> AbstractContextManager\[Any\]

usado dentro do with para abrir um região de transação. No qual define um região que tudo é executado ou nada é executado. Alem disso cuida de commitar sozinho as mudanças, então toda ação no banco é revestido pela transação.

## execute(self, sql: str, params: Params = ()) -> int

Executa um comando sql dentro de uma transação, armazena o cursor resultante e retorna o numero de linhas afetadas. recebe de argumento um comando sql e os parametros.

### execute_many(self, sql: str, params_seq: Sequence\[Params\]) -> int

Executa o mesmo comando sql mas com vários conjuntos de parâmetros, retorna o numero de linhas afetadas e recebe como argumento o comando sql e uma sequencia de conjunto de parâmetros

### execute_script(self, script: str) -> None

Executa o script sql recebido como parâmetro, retorna nada

### insert(self, tabela: str, dados: dict\[str, Any\]) -> int:

Recebe uma tabela e dados do registro, insere um registro na tabela e retorna o id do registro

### fetch_all(self) -> list\[Linha\]

usa o cursor guardo para puxar todo resultado da consulta executada


### fetch_one(self) -> Linha | None:

usa o cursor guardo para recuperar o proximo elemento da fila do resultado da consulta

### fetch_batches(self, tamanho_lote: int = 1000) -> Generator\[list\[Linha\]\]

usa o cursor guardo para recuperar os n proximos elementos da fila do resultado da consulta, recebe com argumento a quantidade máxima de itens a serem retornado


### table_exists(self, tabela: str) -> bool

recebe um nome de uma tabela e verifica se ela existe e retorna a resposta




