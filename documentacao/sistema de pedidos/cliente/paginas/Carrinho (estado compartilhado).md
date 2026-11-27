Objeto único que guarda o carrinho do usuário para as páginas de pedidos. Código: `paginas/sisPedidos/carrinho.py`. Usado pelo [[Página de Catálogo|catálogo]] (que adiciona) e pelo [[Página de Carrinho|carrinho]] (que exibe). Mapa geral em [[Páginas]].

## O que é

`Carrinho` é um `QObject` obtido por `DIC.carrinho()` (Singleton). Os dados ficam **no banco, por usuário**, e são acessados pelo `FacedeCarrinhoAPI` (ver [[Facedes de acesso ao servidor]]). A classe mantém uma **cópia local** em `itens: dict[id da linha → ItemCarrinho]` para as telas lerem sem ir à API a cada redesenho. O mesmo produto pode ter várias linhas, com datas de necessidade ou unidades diferentes.

## Regra de ouro

Toda alteração é gravada **primeiro na API**. Só se der certo a cópia local é trocada pelo que o servidor devolveu. Se falhar, o estado local **não muda** e o sinal `falhou` é emitido com a mensagem.

## Sinais

| Sinal | Quando |
|---|---|
| `alterado()` | os itens locais mudaram |
| `falhou(str)` | uma chamada à API falhou (mensagem = `detalhe` da resposta, ou o erro) |

## Métodos

| Método | O que faz | Retorno |
|---|---|---|
| `recarregar()` | busca o carrinho do usuário na API | `bool` |
| `adicionar(produto, quant, uni, data_necessidade)` | soma ao produto naquela data e unidade; troca a cópia pelo carrinho devolvido | `bool` |
| `remover(ids_itens)` | apaga as linhas e relê o carrinho | `bool` |
| `esquecer()` | descarta só a cópia local, **sem tocar na API** (usado no logout, para o próximo usuário não ver os itens do anterior); emite `alterado` | nada |
| `limpar()` | esvazia o carrinho | `bool` |
| `finalizar(obra, tarefa, local_entrega)` | o servidor cria o pedido com as linhas e esvazia o carrinho; a cópia local fica vazia | `int` (id do pedido) |

Os métodos que devolvem `bool` devolvem `False` quando falham (e emitem `falhou`). **`finalizar` é a exceção**: a falha sobe como `ApiError`, para a tela mostrar um aviso próprio, e o carrinho local não muda.
