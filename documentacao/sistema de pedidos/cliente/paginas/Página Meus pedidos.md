Pedidos feitos pelo usuário e, ao selecionar um, os itens dele. Código: `paginas/sisPedidos/paginaMeusPedidos/paginaMeusPedidos.py`. Mapa geral em [[Páginas]].

## O que faz

Lista **só os pedidos do usuário autenticado**, do mais novo para o mais antigo, com filtro de status. A tela é dividida (`QSplitter` vertical): pedidos em cima, itens do pedido selecionado embaixo.

Usa o `FacedePedidoAPI` (`DIC.facede_pedido()`); ver [[Facedes de acesso ao servidor]].

## Componentes

- **`PaginaMeusPedidos`**:
  - `status`: combo de filtro ("Todos" + os status que o usuário tem).
  - `tabela_pedidos`: Nº, Criado em, Obra, Tarefa, Local de entrega, Status e Itens. Seleção de uma linha.
  - `paginacao_pedidos`: [[Barra de paginação]] **no servidor** (30 por página).
  - `tabela_itens`: Produto, Qtd., Un. e Necessário até.
  - `paginacao_itens`: barra **local** (30 por página).
  - `resumo` e `rotulo_erro`; botão **Atualizar** no topo.
- **`formatar_data_hora(valor)`**: converte a data de criação (gravada em UTC, sem fuso) para o horário local, `dd/mm/aaaa hh:mm`; "—" se não houver data.
- **`_tabela(colunas, stretch)`**: cria as duas tabelas (somente leitura, seleção por linha, cabeçalho alinhado ao conteúdo).

## Funcionamento

### Carregar (`recarregar`)

1. Busca os status distintos dos pedidos do usuário (`status_dos_meus`) e refaz o combo, **mantendo o status escolhido** se ainda existir.
2. Limpa o cache de itens.
3. Carrega a página de pedidos.

Em `ApiError`, mostra "Não foi possível carregar seus pedidos: ..." e mantém o que estava na tela.

### Pedidos (`_carregar_pedidos`)

Chama `listar_meus_pagina(status, limit, offset)`, que devolve `(pedidos, total)`. O filtro de status e a paginação vão **na consulta**, então o servidor só devolve os 30 da página. Se a página pedida ficou além do fim, ajusta para a última existente e consulta de novo (duas tentativas, no máximo).

Mudar o status **volta à primeira página**. Ao redesenhar a tabela, a seleção é limpa. O resumo mostra:

| Situação | Texto |
|---|---|
| Há pedidos | "N pedido(s)" |
| Nenhum, sem filtro | "Você ainda não fez nenhum pedido" |
| Nenhum, com filtro | "Nenhum pedido com esse status" |

### Itens do pedido (`_mostrar_itens`)

- Sem seleção: título "Itens do pedido — selecione um pedido acima" e tabela vazia.
- Com seleção: o id do pedido vem da coluna Nº (`Qt.UserRole`). Os itens são **buscados na primeira vez** (`itens_do_pedido`) e guardados em `_itens_cache`; depois vêm do cache. A tabela mostra uma página por vez, com a barra local voltando à primeira página a cada pedido.
- Falha ao buscar os itens: mostra o erro "Não foi possível carregar os itens do pedido N: ..." e esvazia a tabela de itens.

O cache só é limpo ao atualizar, então os itens de um pedido não mudam na tela até o usuário clicar em **Atualizar**. Um pedido recém-criado na [[Página de Carrinho]] também só aparece depois disso.
