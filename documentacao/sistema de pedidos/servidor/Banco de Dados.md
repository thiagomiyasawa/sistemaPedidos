## Banco de dados usado

- Desenvolvimento/teste: **SQLite** (caminho do arquivo na variável de ambiente `SQLITE`).
- O acesso é sempre pelo [[Adapter do banco de dados]], então o banco pode ser trocado sem afetar o resto do sistema.
- Chaves estrangeiras ligadas (`PRAGMA foreign_keys = ON`).
- O script de criação está em `src/bancoDadosSQL/SQLite/querys/criaTabelas.sql` (**apaga e recria todas as tabelas**).
- Datas são texto em UTC (`YYYY-MM-DD HH:MM:SS`).

## Visão geral

| Grupo | Tabelas | Quem usa |
|---|---|---|
| Pedidos | `pedido`, `item_pedido` | [[Facede pedido]], [[Facede metricas]] |
| Catálogo e carrinho | `produtos`, `carrinho_itens_cadastro` | [[Facede produto]], [[Facede carrinho]] |
| Usuários e acesso | `usuario`, `cargos`, `chavesAPI` | [[Facede autenticacao]] |
| Autorização | `tabelas`, `cargo_permissao`, `usuario_permissao` | [[Facede autorizacao]] |

Relações principais: `pedido.user_id → usuario.id`, `item_pedido.id_pedido → pedido.id`, `carrinho_itens_cadastro.user_id → usuario.id`, `usuario.cargo_id → cargos.id`, `chavesAPI.user_id → usuario.id`.

---

## Pedidos

### pedido

Pedidos feitos.

- `id` → identificação do pedido (autoincremento)
- `user_id` → usuário dono do pedido (FK `usuario`)
- `cod_rm` → identificação do pedido em um sistema externo (nesse caso o RM); opcional
- `num_itens` → quantidade de itens do pedido
- `status_atual` → status atual do pedido
- `data_criacao` → quando foi criado (padrão: agora, UTC)
- `origem` → plataforma em que foi criado
- `local_entrega` → local de entrega
- `obra` → obra da empresa em que o material será entregue
- `tarefa` → tarefa da obra a que o pedido pertence

### item_pedido

Itens de cada pedido. Chave primária composta `(id_pedido, id)`.

- `id` → número do item dentro do pedido (1, 2, 3…)
- `id_pedido` → pedido a que pertence (FK `pedido`)
- `produto` → produto do item (texto, normalmente `codigo - descricao`)
- `quant` → quantidade
- `uni` → unidade de medida (un, m, kg…)
- `data_necessidade` → data em que o produto é necessário

---

## Catálogo e carrinho

### produtos

Produtos cadastrados.

- `id` → identificação do produto
- `codigo` → código externo do produto
- `descricao` → descrição
- `categoria` → categoria

### carrinho_itens_cadastro

Itens que o usuário separou para virar pedido. Único por `(user_id, produto_id, data_necessidade, unidade)`: o mesmo produto repete só com data ou unidade diferentes.

- `id` → identifica a linha (usado para remover)
- `user_id` → dono do carrinho (FK `usuario`)
- `produto_id` → produto (referente a `produtos.id`)
- `quantidade` → quantidade
- `unidade` → unidade de medida
- `data_necessidade` → data em que o produto é necessário

---

## Usuários e acesso

### usuario

Usuários do sistema.

- `id` → identificação do usuário
- `nome` → nome (único)
- `senha` → hash scrypt da senha, nunca o texto puro
- `cargo_id` → cargo do usuário (FK `cargos`)
- `ativo` → `0` aguardando validação / desativado, `1` ativo. Só usuário ativo faz login. O registro novo nasce com `ativo = 0` e cargo `pendente`.

### cargos

- `id` → identificação do cargo
- `nome` → nome do cargo (único, sem diferenciar maiúsculas)

### chavesAPI

Chaves de API emitidas no login para identificar o usuário nas requisições.

- `chave` → chave (chave primária)
- `user_id` → usuário dono da chave (FK `usuario`)
- `DateTime_exp` → vencimento da chave; chave vencida ou sem validade é inválida

---

## Autorização

O cargo define as permissões padrão por tabela; uma linha do usuário para a mesma tabela **substitui** a do cargo.

### tabelas

Tabelas do sistema sobre as quais se concede autorização.

- `nome` → nome da tabela (chave primária, sem diferenciar maiúsculas)

### cargo_permissao

Permissões padrão de um cargo. Chave primária `(cargo_id, tabela)`.

- `cargo_id` → cargo (FK `cargos`)
- `tabela` → tabela (FK `tabelas`)
- `criar` → pode criar registros
- `atualizar` → pode atualizar registros
- `deletar` → pode deletar registros
- `ler` → pode ler registros
- `todos` → alcance: `1` registros de qualquer dono, `0` apenas os próprios

Cada flag vale `0` ou `1`.

### usuario_permissao

Exceções de um usuário, com as mesmas colunas de `cargo_permissao`, trocando `cargo_id` por `user_id` (FK `usuario`). Chave primária `(user_id, tabela)`.
