Lista de produtos para consulta e adição ao carrinho. Código: `paginas/sisPedidos/paginaCatalogo/` (`paginaBase.py` e `dialogoAdicionarItem.py`). Mapa geral em [[Páginas]].

## O que faz

Mostra os produtos com **busca por texto** e **filtro de categoria**. O botão "Adicionar" de cada linha abre um diálogo para informar quantidade, unidade e data de necessidade, e manda o item para o [[Carrinho (estado compartilhado)|carrinho]] compartilhado, exibido na [[Página de Carrinho]].

A **paginação é feita no servidor**: a tela pede à API só os 30 produtos da página atual, já filtrados, e recebe o total para montar a [[Barra de paginação]].

## Componentes

- **`PaginaCatalogo`**: a página. Cuida da API e do carrinho.
  - `catalogo` (`PainelCatalogo`): o painel visual.
  - `carrinho`: carrinho que recebe os itens (padrão `DIC.carrinho()`).
  - `rotulo_erro` e `rotulo_carrinho` (resumo "N item(ns) no carrinho" / "Carrinho vazio").
  - Botão **Recarregar** no topo.
- **`PainelCatalogo`**: busca, combo de categoria, tabela (Código, Descrição, Categoria e o botão), barra de páginas e contagem ("N produto(s)"). **Não conhece a API**: apenas emite sinais e recebe dados.
  - `consultar()`: é preciso buscar de novo a página.
  - `adicionar(Produto, quantidade, unidade, data)`: o usuário confirmou um item.
- **`DialogoAdicionarItem`**: popup de detalhes do item.
- **`JanelaPrincipal` e `main()`**: só para rodar a página sozinha.

## Funcionamento

### Divisão de responsabilidades

```
PainelCatalogo ──consultar──▶ PaginaCatalogo ──listar_pagina──▶ FacedeProdutoAPI
      ▲                              │
      └────── definir_pagina(produtos, total) ◀┘
PainelCatalogo ──adicionar──▶ Carrinho.adicionar ──▶ API
```

Quando busca, categoria ou página mudam, o painel emite `consultar`. A página lê `painel.estado()` (`busca, categoria, limit, offset`), consulta o facede e devolve o resultado com `definir_pagina`.

### Ao abrir

Chama `recarregar()` (categorias do filtro + primeira página) e `carrinho.recarregar()`, que traz o carrinho do usuário guardado no banco.

### Busca e filtro

- Digitar na busca **espera 300 ms** sem novas teclas antes de consultar (evita uma requisição por letra). Enter consulta na hora.
- Mudar busca ou categoria **volta à primeira página**.
- Busca vazia ou categoria "Todas" viram `None` na consulta.
- Ao atualizar as categorias, a escolhida é mantida se ainda existir.

### Carregar a página (`carregar_pagina`)

Se a página pedida ficou além do fim (itens saíram do catálogo), ajusta para a última existente e consulta de novo (no máximo duas tentativas). Em `ApiError`, mostra "Não foi possível carregar o catálogo: ..." e **mantém a lista anterior**.

### Adicionar ao carrinho

1. Clique em "Adicionar" abre o `DialogoAdicionarItem`.
2. Se confirmado (e com unidade), o painel emite `adicionar`, ligado a `Carrinho.adicionar`.
3. O carrinho grava na API; se falhar, emite `falhou` e a página mostra "Erro no carrinho: ..." no resumo. O resumo se atualiza a cada `alterado`.

## DialogoAdicionarItem

Mostra o código e a descrição do produto (e a categoria, se houver) e pede:

| Campo | Regra |
|---|---|
| Quantidade | inteiro de 1 a 1.000.000 (mesmo limite da API); começa em 1 |
| Unidade | combo **editável**: a lista `UNIDADES` são sugestões, mas aceita texto livre (limite `TAM_MAX_UNIDADE`); padrão `UNIDADE_PADRAO` |
| Necessário até | calendário `dd/MM/yyyy`; sugere hoje + 7 dias; entre 2000-01-01 e hoje + 10 anos (como a API) |

O botão **Adicionar ao carrinho** só habilita com a unidade preenchida. Os valores saem por `quantidade()`, `unidade()` (sem espaços nas pontas) e `data_necessidade()`.
