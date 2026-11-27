Telas do [[Cliente]] (PySide6). Esta nota é o **mapa**: diz o que é cada módulo e como as telas se ligam. O funcionamento de cada tela está na nota dela (links abaixo).

Regras que valem para todas as páginas:

- Só conhecem **facedes** e **entidades** (via `DIC`), nunca HTTP. Ver [[Facedes de acesso ao servidor]].
- Falha da API (`ApiError`) vira **mensagem em vermelho na própria página**, mantendo os dados que já estavam na tela.
- Cada página aceita o facede por parâmetro (para teste); sem parâmetro usa o do `DIC`.
- Cada arquivo de página tem um `main()` e roda sozinho; nesse caso não há login, então a chave tem que estar em `MONITORKPI_API_KEY`.

## Módulos

O código está em `src/client/`. As páginas ficam em `paginas/`; o que elas compartilham ficam em outras pastas.

| Módulo            | Pasta                  | O que é                                                                                                                                                                                      |
| ----------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Login**         | `paginas/sistemaLogin` | Tela de entrada: troca usuário e senha por uma chave de API e decide, ao abrir o app, se vai ao login ou direto ao menu.                                                                     |
| **Menu**          | `paginas/sistemaMenu`  | Casca do app: barra lateral com os módulos e a área onde a página escolhida aparece.                                                                                                         |
| **sisPedidos**    | `paginas/sisPedidos`   | Fluxo de **fazer pedidos**: escolher produtos no catálogo, montar o carrinho, finalizar e acompanhar os pedidos. É também o dono do estado do [[Carrinho (estado compartilhado)\|Carrinho]]. |
| **monitorkpi**    | `paginas/monitorkpi`   | Painéis de **indicadores (KPIs)** de pedidos, com gráficos e filtros. Só leitura.                                                                                                            |


### Dentro de `sisPedidos`

| Pasta/arquivo | O que é |
|---|---|
| `paginaCatalogo/` | Página do catálogo (`paginaBase.py`) e o diálogo de adicionar item (`dialogoAdicionarItem.py`). |
| `paginaCarrinho/` | Página do carrinho e o diálogo de novo pedido (`dialogoNovoPedido.py`). |
| `paginaMeusPedidos/` | Página com os pedidos do usuário. |
| `carrinho.py` | Classe `Carrinho`, o estado compartilhado entre catálogo e carrinho. |

### Dentro de `monitorkpi`

O caminho é `paginas/monitorkpi/paginas/paginasPedidos/`.

| Pasta | O que é |
|---|---|
| `paginaPedidosGeral/` | Página dos KPIs da visão geral. |
| `paginaPedidosObra/` | Página dos KPIs de uma obra. |
| `recursosCompartilhados/` | Tudo que as duas páginas usam: `paginaBase.py` (esqueleto), `cartaoGrafico.py` (cartão base dos gráficos), `dadosPedidos.py` (filtros e requisições), `estilo.py` (folha de estilo) e `graficos/` (um módulo por gráfico). |

## Navegação

```
Login ──▶ Menu ──▶ KPIs - Geral
                ├─ KPIs - Por obra
                ├─ Catálogo ──(adiciona)──▶ Carrinho ──(finaliza)──▶ Meus pedidos
                ├─ Carrinho
                └─ Meus pedidos
```

## Notas de cada página

**Entrada e navegação**
- [[Página de Login]]
- [[Página de Menu]]

**Pedidos (`sisPedidos`)**
- [[Página de Catálogo]] (inclui o diálogo de adicionar item)
- [[Página de Carrinho]] (inclui o diálogo de novo pedido)
- [[Página Meus pedidos]]
- [[Carrinho (estado compartilhado)]]

**KPIs (`monitorkpi`)**
- [[KPIs - base e gráficos]]: esqueleto, cartões, dados e os seis gráficos
- [[Página KPIs - Geral]]
- [[Página KPIs - Por obra]]

**Componente**
- [[Barra de paginação]]
