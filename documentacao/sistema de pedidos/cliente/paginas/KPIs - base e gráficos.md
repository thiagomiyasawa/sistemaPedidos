Estrutura comum às páginas de KPIs do [[Cliente]]. Código: `paginas/monitorkpi/paginas/paginasPedidos/recursosCompartilhados/`. As páginas que usam isto: [[Página KPIs - Geral]] e [[Página KPIs - Por obra]]. Mapa geral em [[Páginas]].

## Como as peças se encaixam

```
Página (PaginaKPIBase)            filtros → dicionário ─┐
   │                                                    ▼
   │  aplicar_filtros()  ─────────────▶  carregar_dados(filtros, com_top_itens)
   │                                       │  FacedePedidoAPI.listar_todos   (obra, status)
   │                                       │  filtros locais (origem, tarefa, período)
   │                                       │  FacedeMetricasAPI.top_itens    (se algum gráfico pedir)
   │                                       ▼
   └── c.definir_dados(DadosPedidos) ──▶ cada CartaoGrafico redesenha
```

A página faz as requisições **uma única vez por atualização** e entrega o mesmo resultado a todos os gráficos. Os gráficos nunca consultam a API.

## Arquivos

| Arquivo | O que é |
|---|---|
| `paginaBase.py` | `PaginaKPIBase`: esqueleto da página; `executar()`: abre uma página numa janela própria. |
| `cartaoGrafico.py` | `CartaoGrafico`: cartão base de todo gráfico. |
| `dadosPedidos.py` | Filtros, requisições à API e ordem dos status. |
| `estilo.py` | Folha de estilo (`ESTILO`) das páginas de KPI. |
| `graficos/` | Um módulo por gráfico. |

## PaginaKPIBase

Monta cabeçalho (título e botão **Atualizar tudo**), barra de filtros e uma grade rolável de cartões (`COLUNAS`; as duas páginas usam 1, um gráfico embaixo do outro). No fim do `__init__` chama `aplicar_filtros()`, que faz a primeira consulta.

A subclasse define só o que é seu:

| Método | O que a subclasse faz |
|---|---|
| `criar_cartoes()` | devolve a lista de gráficos, na ordem de exibição |
| `construir_filtros()` | monta a barra com `add_combo` e `add_controle` |
| `filtros_atuais()` | lê a tela e devolve o dicionário de filtros |

Ferramentas da base:

- **`add_combo(chave, rotulo, itens, padrao, ao_mudar)`**: combo de filtro na barra, registrado em `filtros`. Ao mudar, chama `aplicar_filtros` (ou `ao_mudar`).
- **`add_controle(rotulo, widget)`**: qualquer controle com rótulo; devolve o contêiner para poder mostrar/ocultar.
- **`aplicar_filtros()`**: chama `carregar_dados(filtros_atuais(), com_top_itens=...)` e entrega o resultado a cada cartão. O top de itens só é buscado se algum cartão tem `precisa_top_itens = True`. Em `ApiError`, **cada cartão mostra a mensagem de erro** (a exceção não se propaga).

## CartaoGrafico

Cartão com título, barra de opções próprias do gráfico, o gráfico (`QChart`) e o rótulo "Sem dados para os filtros selecionados". Escolhe o tema claro ou escuro do gráfico conforme a paleta do sistema.

- **Opções do gráfico** (não filtram pedidos, só mudam o desenho): `add_combo` e `add_spin`; qualquer mudança chama `atualizar()`. `valor(chave)` lê o valor atual.
- **`definir_dados(dados)`**: recebe os dados da página e redesenha.
- **`atualizar()`**: redesenha com os dados já recebidos; sem dados, mostra a mensagem de vazio.
- **`mostrar_erro(erro)`**: descarta os dados e exibe "Falha ao consultar a API: ...".
- **`pedidos()` e `top_itens()`**: atalhos para os dados recebidos.
- **`barras(...)` e `eixos_categoria(...)`**: ajudantes para os gráficos de barras (série única com rótulos de valor, eixo de categorias e eixo de valores inteiros).
- Cada gráfico implementa `construir_filtros()` (suas opções) e `construir_grafico()` (o desenho).

## Dados (`dadosPedidos.py`)

### Onde cada filtro é aplicado

| Filtro | Onde |
|---|---|
| `obra`, `status` | **no servidor**, na consulta (`listar_todos`) |
| `origem`, `tarefa`, período | **no cliente**, depois de trazer os pedidos |

- Valores vazios ou `"Todos"` são ignorados.
- Filtrar por **tarefa sem obra** lança `ValueError`.
- Período: `dias` (últimos N dias) ou `de`/`ate` (inclusivos). `data_criacao` chega em UTC, sem fuso, e é comparada em UTC.
- Períodos prontos (`PERIODOS`): "Todo o período", últimos 7, 30 e 90 dias. Padrão: **últimos 7 dias**.

### Funções

- **`carregar_dados(filtros, com_top_itens)`**: devolve `DadosPedidos(pedidos, top_itens)`.
- **`filtrar_pedidos(filtros)`**: a consulta de pedidos descrita acima.
- **`top_itens(filtros, limite)`**: top de produtos, **calculado no servidor** (`FacedeMetricasAPI.top_itens`), com os mesmos filtros. O limite é `LIMITE_TOP_ITENS` (20).
- **`valores_distintos(coluna)`**: opções dos combos (`obra`, `status_atual`, `origem`), lidas numa só requisição (`valores_filtros`) e **guardadas em cache**. Se a API falhar, devolve lista vazia (o erro aparece ao atualizar os gráficos).
- **`tarefas_da_obra(obra)`**: tarefas da obra; a obra é obrigatória (`ValueError`); lista vazia se a API falhar.
- **`chave_status(status)`**: ordenação pela ordem do processo `ORDEM_STATUS` = novo → em cotação → aprovado → em entrega → entregue. Status desconhecidos vão ao fim, em ordem alfabética.

As rotas de métricas exigem a flag `todos` em `pedido` (ver [[Facede autorizacao]]); sem ela o servidor responde 403 e os cartões mostram o erro.

## Gráficos (`graficos/`)

Todos derivam de `CartaoGrafico`.

| Gráfico | Título | Desenho | Opção própria | Usado em |
|---|---|---|---|---|
| `PedidosPorStatus` | Pedidos por status | barras, na ordem do processo | nenhuma | Geral e Por obra |
| `PedidosPorObra` | Pedidos por obra | barras horizontais | nenhuma | Geral |
| `EvolucaoPedidos` | Evolução de pedidos criados | linha no tempo | **Agrupar por**: Dia ou Mês | Geral e Por obra |
| `TopProdutos` | Produtos mais solicitados (quantidade) | barras horizontais | **Top**: de 3 a 20 (padrão 5) | Geral e Por obra |
| `StatusPorObra` | Status por obra (empilhado) | barras empilhadas | nenhuma | Geral |
| `PedidosPorOrigem` | Pedidos por origem | pizza | nenhuma | nenhuma das duas páginas (disponível para uso) |

`TopProdutos` é o único com `precisa_top_itens = True`: só ele depende do top de itens do servidor; os demais contam os pedidos já filtrados no cliente.
