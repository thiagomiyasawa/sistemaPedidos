-- Permissões iniciais. Rode DEPOIS de criaTabelas.sql (que recria as tabelas vazias).
-- Não é idempotente: rodar de novo sem recriar as tabelas falha por chave duplicada.
-- Dados iniciais (ajuste conforme os cargos reais). 'pendente' é o cargo dado no
-- registro e não tem permissão alguma, até alguém validar o usuário.
INSERT INTO tabelas(nome) VALUES ('pedido'), ('item_pedido'), ('usuario'), ('usuario_permissao');
INSERT INTO cargos(nome) VALUES ('admin'), ('comprador'), ('visualizador'), ('pendente'), ('requerente');

INSERT INTO cargo_permissao(cargo_id, tabela, criar, atualizar, deletar, ler, todos) VALUES
    ((SELECT id FROM cargos WHERE nome = 'admin'), 'pedido',            1, 1, 1, 1, 1),
    ((SELECT id FROM cargos WHERE nome = 'admin'), 'item_pedido',       1, 1, 1, 1, 1),
    ((SELECT id FROM cargos WHERE nome = 'admin'), 'usuario',           0, 1, 0, 1, 1),
    ((SELECT id FROM cargos WHERE nome = 'admin'), 'usuario_permissao', 1, 1, 1, 1, 1),
    ((SELECT id FROM cargos WHERE nome = 'comprador'), 'pedido',        1, 1, 0, 1, 0),
    ((SELECT id FROM cargos WHERE nome = 'comprador'), 'item_pedido',   1, 1, 0, 1, 0),
    ((SELECT id FROM cargos WHERE nome = 'visualizador'), 'pedido',      0, 0, 0, 1, 1),
    ((SELECT id FROM cargos WHERE nome = 'visualizador'), 'item_pedido', 0, 0, 0, 1, 1),
    -- requerente: faz pedidos e acompanha só os seus (todos = 0); não edita nem apaga.
    ((SELECT id FROM cargos WHERE nome = 'requerente'), 'pedido',      1, 0, 0, 1, 0),
    ((SELECT id FROM cargos WHERE nome = 'requerente'), 'item_pedido', 1, 0, 0, 1, 0);
