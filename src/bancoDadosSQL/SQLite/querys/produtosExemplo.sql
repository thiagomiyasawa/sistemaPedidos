-- Produtos de exemplo para o catálogo (tabela `produtos`). Rode DEPOIS de criaTabelas.sql.
-- Não é idempotente: rodar de novo duplica os produtos.
INSERT INTO produtos(codigo, descricao, categoria) VALUES
    ('EL-001', 'Cabo flexível 2,5 mm² (rolo 100 m)', 'Elétrica'),
    ('EL-002', 'Disjuntor monopolar 20 A', 'Elétrica'),
    ('EL-003', 'Eletroduto corrugado 3/4"', 'Elétrica'),
    ('HI-001', 'Tubo PVC soldável 25 mm (barra 6 m)', 'Hidráulica'),
    ('HI-002', 'Registro de esfera 3/4"', 'Hidráulica'),
    ('HI-003', 'Cola para PVC 175 g', 'Hidráulica'),
    ('CV-001', 'Cimento CP-II 50 kg', 'Civil'),
    ('CV-002', 'Areia média', 'Civil'),
    ('CV-003', 'Vergalhão CA-50 10 mm (barra 12 m)', 'Civil'),
    ('EP-001', 'Capacete de segurança', 'EPI'),
    ('EP-002', 'Luva de raspa', 'EPI'),
    ('EP-003', 'Óculos de proteção', 'EPI');
