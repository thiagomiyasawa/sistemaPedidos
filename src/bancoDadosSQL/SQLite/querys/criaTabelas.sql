DROP TABLE IF EXISTS item_pedido;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS carrinho_itens_cadastro;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS chavesAPI;
DROP TABLE IF EXISTS usuario_permissao;
DROP TABLE IF EXISTS cargo_permissao;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS cargos;
DROP TABLE IF EXISTS tabelas;

-- Tabelas do sistema sobre as quais se concede autorização.
CREATE TABLE tabelas(
    nome TEXT PRIMARY KEY COLLATE NOCASE
);

CREATE TABLE cargos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE usuario(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    cargo_id INTEGER NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 0 CHECK(ativo in (0,1)),
    CONSTRAINT fk_cargo_id FOREIGN KEY(cargo_id) REFERENCES cargos(id)
);

CREATE TABLE chavesAPI(
    chave TEXT PRIMARY KEY,
    user_id INTEGER,
    DateTime_exp DATETIME,
    CONSTRAINT fk_user_id FOREIGN KEY(user_id) REFERENCES usuario(id)
);

-- Autorização por tabela: o cargo define o padrão; a linha do usuário (se existir
-- para a tabela) SUBSTITUI a do cargo. `todos` = vale para registros de qualquer
-- dono, não só os do próprio usuário (ex.: ver pedidos de outros usuários).
CREATE TABLE cargo_permissao(
    cargo_id INTEGER NOT NULL,
    tabela TEXT NOT NULL COLLATE NOCASE,
    criar INTEGER NOT NULL DEFAULT 0 CHECK(criar in (0,1)),
    atualizar INTEGER NOT NULL DEFAULT 0 CHECK(atualizar in (0,1)),
    deletar INTEGER NOT NULL DEFAULT 0 CHECK(deletar in (0,1)),
    ler INTEGER NOT NULL DEFAULT 0 CHECK(ler in (0,1)),
    todos INTEGER NOT NULL DEFAULT 0 CHECK(todos in (0,1)),
    PRIMARY KEY(cargo_id, tabela),
    CONSTRAINT fk_cargo FOREIGN KEY (cargo_id) REFERENCES cargos(id),
    CONSTRAINT fk_tabela FOREIGN KEY(tabela) REFERENCES tabelas(nome)
);

CREATE TABLE usuario_permissao(
    user_id INTEGER NOT NULL,
    tabela TEXT NOT NULL COLLATE NOCASE,
    criar INTEGER NOT NULL DEFAULT 0 CHECK(criar in (0,1)),
    atualizar INTEGER NOT NULL DEFAULT 0 CHECK(atualizar in (0,1)),
    deletar INTEGER NOT NULL DEFAULT 0 CHECK(deletar in (0,1)),
    ler INTEGER NOT NULL DEFAULT 0 CHECK(ler in (0,1)),
    todos INTEGER NOT NULL DEFAULT 0 CHECK(todos in (0,1)),
    PRIMARY KEY(user_id, tabela),
    CONSTRAINT fk_user_id FOREIGN KEY(user_id) REFERENCES usuario(id),
    CONSTRAINT fk_tabela FOREIGN KEY(tabela) REFERENCES tabelas(nome)
);

CREATE TABLE pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    cod_rm INTEGER,
    num_itens INTEGER NOT NULL,
    status_atual TEXT NOT NULL,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    origem TEXT NOT NULL,
    local_entrega TEXT NOT NULL,
    obra TEXT NOT NULL,
    tarefa TEXT NOT NULL ,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES usuario(id)
);
CREATE TABLE item_pedido(
    id INTEGER NOT NULL,          -- número do item dentro do pedido (1, 2, 3...)
    id_pedido INTEGER NOT NULL,
    produto TEXT NOT NULL,
    quant INTEGER NOT NULL,
    uni TEXT NOT NULL,            -- unidade de medida (un, m, kg...)
    data_necessidade DATE NOT NULL,
    PRIMARY KEY (id_pedido, id),
    CONSTRAINT fk_id_pedido FOREIGN KEY (id_pedido) REFERENCES pedido(id)
);
CREATE TABLE produtos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT,
    descricao TEXT,
    categoria TEXT
);
CREATE TABLE carrinho_itens_cadastro(
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- identifica a linha (para remover)
    user_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    unidade TEXT NOT NULL,
    data_necessidade DATE NOT NULL,
    -- o mesmo produto pode repetir, desde que em data de necessidade ou unidade diferentes
    UNIQUE (user_id, produto_id, data_necessidade, unidade),
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES usuario(id)
);
