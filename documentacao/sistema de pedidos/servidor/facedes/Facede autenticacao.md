Decide se uma requisição é de um usuário conhecido: registra usuários, faz login emitindo chave de API e valida a chave. Consome o [[Adapter do banco de dados]]. Implementa `facedeAutenticacaoInterface`. A parte de "o que o usuário pode fazer" está no [[Facede autorizacao]].

Tabelas: `usuario` (nome, senha, cargo_id, ativo), `cargos` e `chavesAPI` (chave, user_id, DateTime_exp).

```python
with DIC.db() as db:
    f = FacedeAutenticacao(db)
    chave, expira = f.login("ana", "segredo")
    identidade = f.autenticar(chave)
```

## constantes

- `VALIDADE_PADRAO = 8 horas` — duração da chave emitida no login (configurável no construtor).
- `CARGO_PENDENTE = "pendente"` — cargo dado no registro, sem permissões; precisa existir em `cargos`.

## segurança

- Senha guardada como hash **scrypt** com sal aleatório: `scrypt$<sal>$<hash>`.
- A conferência usa `hmac.compare_digest` (tempo constante).
- Se o usuário não existe, a senha é conferida contra um hash falso, para o tempo de resposta não revelar se o nome é válido.
- Usuário inativo recebe a mesma resposta de credencial inválida, só depois de conferir a senha.
- Datas em UTC, como o `datetime('now')` do SQLite.

## funções do módulo

### hash_senha(senha: str) -> str

Gera o hash para guardar em `usuario.senha`.

### \_confere_senha(senha, guardado) -> bool

Compara a senha com o hash guardado. Formato inválido ou `None` retorna False.

## FacedeAutenticacao

### registrar(self, nome: str, senha: str) -> int | None

Cria usuário novo **inativo** (`ativo = 0`) com cargo `pendente`, até alguém validar (ver `atualizar_usuario` no [[Facede autorizacao]]). A checagem de nome repetido (sem diferenciar maiúsculas) acontece no próprio `INSERT`. Retorna o id criado, ou `None` se o nome já estiver em uso.

### login(self, nome: str, senha: str) -> tuple\[str, datetime\] | None

Valida usuário e senha. Em uma transação: apaga as chaves vencidas do usuário; se ainda houver chave vigente, devolve a de maior validade; senão emite uma nova (`_emitir`). Retorna `(chave, vencimento UTC)` ou `None` (usuário inexistente, inativo ou senha incorreta).

### \_emitir(self, user_id: int) -> tuple\[str, datetime\]

Interna. Gera chave aleatória (`secrets.token_urlsafe(32)`) e grava em `chavesAPI` com o vencimento.

### logout(self, chave: str) -> bool

Revoga a chave. True se ela existia.

### autenticar(self, chave: str | None) -> Identidade | None

Valida a chave em uma consulta só. Retorna `Identidade(user_id, cargo_id, cargo)` se a chave existe, não venceu e o usuário está ativo; senão `None`. Efeito colateral: chave vencida apresentada é apagada.
