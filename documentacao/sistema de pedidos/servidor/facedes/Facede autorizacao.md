Autorização por tabela e ação, mais a administração de usuários. Consome o [[Adapter do banco de dados]]. Implementa `facedeAutorizacaoInterface`. A identificação do usuário vem do [[Facede autenticacao]].

## modelo de permissões

Cada permissão (`Permissao`) tem cinco flags: `criar`, `atualizar`, `deletar`, `ler` e `todos` (agir sobre dados de outros usuários).

- `cargo_permissao`: padrão do cargo, por tabela.
- `usuario_permissao`: exceção do usuário, por tabela. Se existir linha para a tabela, ela **substitui** a do cargo (pode negar o que o cargo concede e conceder o que ele não concede).

```python
with DIC.db() as db:
    perms = FacedeAutorizacao(db).permissoes(user_id=1, cargo_id=2)
    perms["pedido"].permite("criar")
```

## funções

### permissoes(self, user_id: int, cargo_id: int) -> dict\[str, Permissao\]

Permissões efetivas: nome da tabela (minúsculo) → `Permissao`. Uma consulta só: linhas do usuário mais as do cargo nas tabelas em que o usuário não tem linha.

### obter_usuario(self, user_id: int) -> dict | None

Dados públicos (`id`, `nome`, `cargo_id`, `cargo`, `ativo`), **nunca a senha**. `None` se não existir.

### listar_usuarios(self, apenas_pendentes: bool = False) -> list\[dict\]

Lista usuários por id, sem a senha. Com `apenas_pendentes=True`, só os inativos (aguardando validação do registro).

### atualizar_usuario(self, user_id, ativo=None, cargo=None) -> bool

Ativa/desativa e/ou troca o cargo (pelo nome). Retorna True se o usuário existe. Lança `ValueError` se nada for informado ou se o cargo não existir.

### definir_permissao_usuario(self, user_id, tabela, permissao) -> bool

Cria ou substitui (upsert) a exceção do usuário para a tabela. A tabela precisa estar cadastrada em `tabelas` (senão `ValueError`). Retorna False se o usuário não existir.

### remover_permissao_usuario(self, user_id, tabela) -> bool

Apaga a exceção do usuário; volta a valer a permissão do cargo. True se havia linha.
