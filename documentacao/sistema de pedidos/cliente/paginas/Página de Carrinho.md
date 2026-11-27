Itens escolhidos no catálogo, com remoção e finalização do pedido. Código: `paginas/sisPedidos/paginaCarrinho/` (`paginaCarrinho.py` e `dialogoNovoPedido.py`). Mapa geral em [[Páginas]].

## O que faz

Exibe o conteúdo do [[Carrinho (estado compartilhado)|carrinho]] (o mesmo objeto usado pelo [[Página de Catálogo|catálogo]]) e permite **remover linhas**, **limpar** tudo e **finalizar o pedido**. Quem monta o pedido é o servidor; a tela só pede os dados que o carrinho não tem.

## Componentes

- **`PaginaCarrinho`**:
  - `tabela`: Código, Descrição, Qtd., Un. e Necessário até; seleção de várias linhas.
  - `paginacao`: [[Barra de paginação]] local (30 linhas por página).
  - `resumo`: "N item(ns) distintos" ou "Carrinho vazio".
  - `rotulo_erro`: última falha da API.
  - Botões **Remover selecionados**, **Limpar** e **Finalizar pedido** (`finalizar`, desabilitado com o carrinho vazio).
- **`DialogoNovoPedido`**: formulário de obra, tarefa e local de entrega.
- **`DadosPedido`**: `dataclass` imutável (`obra`, `tarefa`, `local_entrega`) que o diálogo devolve.

## Funcionamento

### Acompanha o carrinho

A página não guarda dados: ao receber o sinal `alterado` do carrinho, chama `redesenhar()`; ao receber `falhou(mensagem)`, mostra "Erro no carrinho: ..." em vermelho. Ao abrir, desenha o que há e chama `carrinho.recarregar()` para trazer o carrinho do usuário guardado no banco.

### `redesenhar()`

1. Esconde o erro.
2. Pega as linhas do carrinho (ordem de inclusão) e informa o total à barra de páginas (a página atual é mantida e ajustada se a lista encolheu).
3. Preenche a tabela só com a fatia da página atual. O **id da linha do carrinho** fica guardado na coluna do código (`Qt.UserRole`), para saber o que remover.
4. Atualiza o resumo e habilita ou desabilita "Finalizar pedido".

### Remover e limpar

- **Remover selecionados**: coleta os ids das linhas selecionadas e chama `carrinho.remover(ids)`.
- **Limpar**: liga direto em `carrinho.limpar`.

Em ambos, se a API falhar o estado local não muda e o erro aparece em vermelho.

### Finalizar pedido (`_finalizar`)

1. Abre o `DialogoNovoPedido`, que informa quantos itens distintos serão enviados.
2. Se o usuário cancelar, nada acontece.
3. Chama `carrinho.finalizar(obra, tarefa, local_entrega)`. O servidor cria o pedido com as linhas do carrinho e as apaga (status inicial e origem são definidos lá).
4. Sucesso → mensagem "Pedido nº X criado com N item(ns)." e o carrinho local fica vazio.
5. `ApiError` → aviso "Não foi possível criar o pedido: ..." com o motivo (permissão, validação, rede). **O carrinho continua como estava.**

`finalizar` é o único método do carrinho que lança a exceção em vez de emitir `falhou`: por ser uma ação pedida pelo usuário, ela merece um aviso próprio.

O pedido criado aparece depois em [[Página Meus pedidos]] (botão Atualizar).

## DialogoNovoPedido

| Campo | Limite |
|---|---|
| Obra | 150 caracteres |
| Tarefa | 150 caracteres |
| Local de entrega | 250 caracteres |

O botão **Criar pedido** só habilita quando os três têm texto (sem contar espaços). `dados()` devolve os textos já aparados.
