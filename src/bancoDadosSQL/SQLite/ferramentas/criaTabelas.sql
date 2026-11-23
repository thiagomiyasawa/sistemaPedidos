DROP TABLE IF EXISTS pedido;

CREATE TABLE pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cod_rm INTEGER,
    num_itens INTEGER NOT NULL,
    status_atual TEXT NOT NULL,
    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    origem TEXT NOT NULL,
    local_entrega TEXT NOT NULL,
    obra TEXT NOT NULL,
    tarefa TEXT NOT NULL 
);

DROP TABLE IF EXISTS item_pedido;

CREATE TABLE item_pedido(
    id INTEGER NOT NULL,          -- número do item dentro do pedido (1, 2, 3...)
    id_pedido INTEGER NOT NULL,
    produto TEXT NOT NULL,
    quant INTEGER NOT NULL,
    data_necessidade DATE,
    PRIMARY KEY (id_pedido, id),
    CONSTRAINT fk_item_pedido FOREIGN KEY (id_pedido) REFERENCES pedido(id)
);
