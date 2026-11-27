Painel de indicadores de pedidos de **uma obra**. Código: `paginas/monitorkpi/paginas/paginasPedidos/paginaPedidosObra/paginaObra.py`. Item do menu: **KPIs - Por obra**. Mapa geral em [[Páginas]]; a estrutura compartilhada está em [[KPIs - base e gráficos]].

## O que faz

Escolhe-se uma obra e os gráficos mostram só os pedidos dela. Tarefa, status, origem e período filtram em conjunto. Reaproveita só os gráficos que fazem sentido para uma única obra.

## Componentes

- **`PaginaKPIPedidosObra`**: subclasse de `PaginaKPIBase`, título "KPIs de Pedidos por Obra", 1 coluna.
  - `data_de` e `data_ate`: campos de data do período personalizado.
  - `caixa_de` e `caixa_ate`: contêineres desses campos (visíveis só no período personalizado).
- **`PERSONALIZADO`**: opção extra do combo de período.
- **`main()`**: abre a página sozinha, sem login (chave em `MONITORKPI_API_KEY`).

## Gráficos (nesta ordem)

1. `PedidosPorStatus`
2. `EvolucaoPedidos`
3. `TopProdutos`

## Filtros

| Filtro | Comportamento |
|---|---|
| Obra | lista das obras existentes; **não tem "Todos"**: sempre há uma obra selecionada (a primeira da lista) |
| Tarefa | "Todos" + tarefas **da obra escolhida** |
| Status | "Todos" + status existentes, na ordem do processo |
| Origem | "Todos" + origens existentes |
| Período | Todo o período, 7, 30 ou 90 dias (padrão 7) ou **Personalizado** |
| De / Até | só aparecem com "Personalizado"; iniciam em hoje − 7 dias e hoje |

## Funcionamento

### Obra e tarefa

A tarefa só existe dentro de uma obra. Ao abrir, as tarefas são as da primeira obra. Ao **trocar a obra** (`obra_mudou`), o combo de tarefa é refeito com as tarefas da nova obra (voltando a "Todos", sem disparar consulta no meio) e só então a página consulta.

### Período personalizado

- Selecionar "Personalizado" mostra os campos De e Até (`_atualizar_datas`); qualquer outro período os esconde.
- Mudar uma das datas consulta de novo.
- Se De for maior que Até, a página **troca os dois** (usa o menor como início e o maior como fim).
- Em período pronto, o filtro vai como `dias`; no personalizado, como `de`/`ate` (datas inclusivas).

### Consulta

`filtros_atuais()` devolve `{obra, tarefa, status, origem}` mais o período. `obra` e `status` vão **ao servidor**; origem, tarefa e período são aplicados **no cliente**. O top de itens é calculado no servidor com os mesmos filtros, por causa do `TopProdutos`. Se a API falhar, todos os cartões mostram a mensagem de erro.

Veja a [[Página KPIs - Geral]] para a visão de todas as obras.
