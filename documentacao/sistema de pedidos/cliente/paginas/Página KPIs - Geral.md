Painel de indicadores de pedidos, visão geral. Código: `paginas/monitorkpi/paginas/paginasPedidos/paginaPedidosGeral/paginaGeral.py`. Item do menu: **KPIs - Geral**. Mapa geral em [[Páginas]]; a estrutura compartilhada está em [[KPIs - base e gráficos]].

## O que faz

Mostra todos os pedidos, de todas as obras, em cinco gráficos. Tudo obedece a um filtro geral de status, origem e período. É só leitura.

## Componentes

- **`PaginaKPIPedidos`**: subclasse de `PaginaKPIBase`, título "KPIs de Pedidos", 1 coluna (um gráfico embaixo do outro).
- **`main()`**: abre a página sozinha (`executar`), sem login; a chave precisa estar em `MONITORKPI_API_KEY`.

## Gráficos (nesta ordem)

1. `PedidosPorStatus`
2. `PedidosPorObra`
3. `EvolucaoPedidos`
4. `TopProdutos`
5. `StatusPorObra`

## Filtros

| Filtro | Opções |
|---|---|
| Status | "Todos" + os status existentes, na ordem do processo |
| Origem | "Todos" + as origens existentes |
| Período | Todo o período, Últimos 7, 30 ou 90 dias (padrão: **7 dias**) |

Não há filtro de obra nem de tarefa: para isso existe a [[Página KPIs - Por obra]].

## Funcionamento

1. Ao abrir, as opções dos combos são lidas da API (uma requisição, depois em cache) e a página já faz a primeira consulta.
2. Trocar qualquer filtro chama `aplicar_filtros()`: `filtros_atuais()` devolve `{status, origem, dias}` e `carregar_dados` busca os pedidos e o top de itens (porque `TopProdutos` precisa dele).
3. `status` vai **ao servidor**; `origem` e o período são aplicados **no cliente**.
4. Cada gráfico redesenha com os mesmos dados. **Atualizar tudo** repete a consulta.
5. Se a API falhar, todos os cartões mostram a mensagem de erro.

Os combos são montados uma vez; se aparecer um status ou uma origem nova no banco, só entra na lista ao reabrir a página (as opções ficam em cache).
