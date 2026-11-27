Componente reutilizável de paginação. Código: `componentes/barraPaginacao.py`. Usado por [[Página de Catálogo]], [[Página de Carrinho]] e [[Página Meus pedidos]]. Mapa geral em [[Páginas]].

## O que é

`BarraPaginacao` mostra os botões « ‹ › » e o texto "Página X de Y · a–b de N". Ela só controla **qual fatia da lista deve ser mostrada**; quem a usa continua dono dos dados. Fica **oculta** quando tudo cabe numa página (`total <= tamanho`).

## Estado

| Atributo | Significado |
|---|---|
| `tamanho` | itens por página (padrão 30; deve ser ≥ 1, senão `ValueError`) |
| `pagina` | página atual, a partir de 0 |
| `total` | quantidade total de itens |
| `paginas` | `ceil(total / tamanho)`, no mínimo 1 |
| `inicio` | índice do primeiro item da página (`pagina * tamanho`) |

Sinal `mudou()`: emitido **só quando o usuário** troca de página, nunca ao chamar `definir_total` ou `voltar_ao_inicio`.

## Métodos

- **`definir_total(total, resetar=False)`**: informa o total. Mantém a página atual, ajustando se a lista encolheu; com `resetar=True` volta à primeira.
- **`voltar_ao_inicio()`**: vai à primeira página sem emitir `mudou` (o chamador já vai consultar de novo).
- **`fatia(itens)`**: devolve os itens da página atual (modo local).
- **`ir_para(pagina)`**: vai para a página (limitada ao intervalo válido) e emite `mudou` se ela mudou.

## Dois modos de uso

**Local**, com a lista inteira já carregada ([[Página de Carrinho]], itens em [[Página Meus pedidos]]):

```python
self.paginacao.mudou.connect(self.desenhar)
self.paginacao.definir_total(len(itens))
for item in self.paginacao.fatia(itens): ...
```

**No servidor** ([[Página de Catálogo]], pedidos em [[Página Meus pedidos]]): `definir_total` recebe o total devolvido pela API; `inicio` e `tamanho` viram o `offset` e o `limit` da consulta; `mudou` dispara a nova consulta e `fatia` não é usada.
