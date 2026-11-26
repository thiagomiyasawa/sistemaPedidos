
## Bando de dados usado
 - teste -> SQLite


## Estrutura do Banco de dados

### Pedidos

Tabela para registro dos pedido feitos

- id -> identificação pedido
- user_id -> identificação usuário relacionado ao pedido
- cod_rm -> identificação do pedido em um sistema externo(Nesse caso Rm)
- num_itens-> quantidade itens nesse pedido
- status_atual -> status atual do pedido
- data_criacao-> data que o pedido foi criado
- origem -> em que plataforma foi criado.
- local_entrega -> local para entrega do pedido
- obra -> em que obra da empresa será entregue o material
- tarefa-> para qual tarefa da obra faz parte esse pedido
### Itens pedido

Tabela para registro dos itens dos pedidos feitos

- id -> identificação do item dentro do pedido
- id_pedido-> identificação do pedido
- produto -> identificação do produto que o item se refere
- quant -> quantidade do produto
- uni-> unidade de medida do produto
- data de necessidade -> data de necessidade do produto
### Carrinho itens cadastro

Registro dos itens registrados no carrinho

- id -> identificação do item do carrinho
- user_id -> identificação do usuário
- produto_id-> identificação do produto
- quantidade -> quantidade de produto
- unidade -> unidade de medida da quantidade
- data necessidade -> data de necessidade do produto
### Produto

Registro dos produtos cadastrados

- id -> identificação do produto
- codigo -> identificação do produto externa
- descrição-> descrição do produto
- categoria -> categoria do produto

### Usuario

registros dos usuário do sistema

- id -> identificação do usuario
- nome -> nome do usuario
- senha -> senha de acesso do usuario(hasheada)
- cargo_id -> identificação do cargo do usuario
- ativo -> estado do registro do usuario

### Cargos 

registros dos cargos dos usuários

- id -> identificação do registro do cargo
- nome -> nome do cargo

### Tabela

registros das tabelas 

- nome -> identificado e nome da tabela do banco de dados

## cargo permissao

tabela para registro das permissões dados a um cargo

- cargo_id -> identificação do cargo
- tabela -> identificação da tabela
- criar -> flag de autorização de criação de registros
- atualizar ->flag de autorização de atualização de registros
- deletar -> flag de autorização de deletar registros
- ler -> flag de autorização leitura de registros 
- todos -> flag de limitação de acesso(todos ou apenas os meus)

## Usuario permissao

tabela para registro das permissões dadas ao usuarios

- usuário-> identificação do cargo
- tabela -> identificação da tabela
- criar -> flag de autorização de criação de registros
- atualizar ->flag de autorização de atualização de registros
- deletar -> flag de autorização de deletar registros
- ler -> flag de autorização leitura de registros 
- todos -> flag de limitação de acesso(todos ou apenas os meus)

### ChaveAPI

tabela para registro da chaves de API para facilitar a identificação

- chave -> chave de api para um usuário
- usuario_id -> identificação do usuário
- DateTime_exp-> data de expiração da chave

