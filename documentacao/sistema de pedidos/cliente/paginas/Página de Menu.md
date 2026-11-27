Casca do [[Cliente]] depois do login. Código: `paginas/sistemaMenu/paginaMenu.py`. Mapa geral em [[Páginas]].

## O que faz

Mostra uma **barra lateral** (220 px) com os módulos e, ao lado, a página escolhida. Não tem conteúdo próprio: só cria e alterna as outras páginas.

## Componentes

- **`PaginaMenu`** (`QWidget`):
  - `botoes`: um botão marcável por módulo, exclusivos entre si (`QButtonGroup`).
  - `pilha`: `QStackedWidget` com as páginas já criadas.
  - `botao_sair`: botão **Sair**, no pé da barra lateral.
  - Sinal `sair()`: emitido ao clicar em Sair.
- **`ENTRADAS`**: lista `(título, fábrica da página)` que define o menu. Para um módulo novo, basta acrescentar uma linha. A `PaginaMenu` também aceita outra lista por parâmetro.

| Item | Página aberta |
|---|---|
| KPIs - Geral | [[Página KPIs - Geral]] |
| KPIs - Por obra | [[Página KPIs - Por obra]] |
| Catálogo | [[Página de Catálogo]] |
| Carrinho | [[Página de Carrinho]] |
| Meus pedidos | [[Página Meus pedidos]] |

## Funcionamento

### Criação sob demanda

Cada página só é criada na **primeira vez** que o item é selecionado, e depois **reaproveitada** (guardada em `_paginas`, indexada pela posição). Isso importa porque várias páginas consultam a API ao nascer. Consequência: voltar a uma página não recarrega os dados; para isso cada página tem seu botão de atualizar.

As fábricas importam a página dentro da função, então o módulo de uma página só é carregado quando o usuário o abre.

### `selecionar(indice)`

1. Marca o botão.
2. Se a página ainda não existe, chama a fábrica e a coloca na pilha.
3. Exibe a página.

### Falha ao criar uma página

Qualquer exceção da fábrica (por exemplo, a API fora do ar) vira um aviso em vermelho no lugar da página: `Não foi possível abrir "<módulo>": <erro>`. O aviso **não é guardado**: a criação é tentada de novo na próxima seleção. Quando o usuário troca de página, o aviso anterior é removido da pilha.

### Sair

O menu **não encerra a sessão**: o botão só emite `sair`, e quem hospeda o menu faz o logout e troca a tela. No app completo, isso é feito pelo `main()` da [[Página de Login]] (revoga a chave, apaga a sessão guardada, esquece o carrinho local e volta ao login). Veja [[Autenticação e sessão]]. Na execução isolada do menu, Sair apenas fecha a janela.

### Chave de API

As páginas usam o adapter compartilhado (`DIC.api`), que já recebeu a chave no login. O menu não faz nada com ela.

## Execução isolada

`main()` abre só o menu numa janela de 1200×800, **sem login**: a chave precisa estar em `MONITORKPI_API_KEY`. Sair apenas fecha a janela.
