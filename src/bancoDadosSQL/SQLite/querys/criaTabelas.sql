DROP TABLE IF EXISTS item_pedido;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS carrinho_itens_cadastro;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS chavesAPI;
DROP TABLE IF EXISTS usuario_permissao;
DROP TABLE IF EXISTS cargo_permissao;
DROP TABLE IF EXISTS usuario;

CREATE TABLE usuario(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE ,
    senha TEXT NOT NULL,
    cargo TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 0 CHECK(ativo in (0,1))
);

CREATE TABLE chavesAPI(
    chave TEXT PRIMARY KEY,
    user_id INTEGER,
    DateTime_exp DATETIME,
    CONSTRAINT fk_user_id FOREIGN KEY(user_id) REFERENCES usuario(id)
);

-- Autorização: permissões por cargo + exceções por usuário.
-- Permissão efetiva = permissões do cargo + concedidas ao usuário - negadas ao usuário.
CREATE TABLE cargo_permissao(
    cargo TEXT NOT NULL COLLATE NOCASE,
    permissao TEXT NOT NULL,
    PRIMARY KEY(cargo, permissao)
);

CREATE TABLE usuario_permissao(
    user_id INTEGER NOT NULL,
    permissao TEXT NOT NULL,
    concedida INTEGER NOT NULL CHECK(concedida in (0,1)),  -- 1 concede, 0 nega
    PRIMARY KEY(user_id, permissao),
    CONSTRAINT fk_user_id FOREIGN KEY(user_id) REFERENCES usuario(id)
);

-- Permissões iniciais (ajuste conforme os cargos reais). Cargo sem linhas aqui
-- (ex.: 'pendente', dado no registro) não acessa nada.
INSERT INTO cargo_permissao(cargo, permissao) VALUES
    ('admin', 'pedidos:ler'), ('admin', 'pedidos:criar'), ('admin', 'pedidos:alterar'),
    ('admin', 'pedidos:remover'), ('admin', 'pedidos:todos'), ('admin', 'metricas:ler'),
    ('admin', 'usuarios:gerenciar'),
    ('comprador', 'pedidos:ler'), ('comprador', 'pedidos:criar'), ('comprador', 'pedidos:alterar'),
    ('visualizador', 'pedidos:ler'), ('visualizador', 'metricas:ler');

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
    data_necessidade DATE,
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
    user_id INTEGER,
    produto_id INTEGER,
    quantidade INTEGER,
    unidade TEXT,
    data_necessidade DATE,
    PRIMARY KEY(user_id,produto_id)
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES usuario(id)
);
