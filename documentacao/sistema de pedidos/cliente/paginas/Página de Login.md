Tela de entrada do [[Cliente]]. Código: `paginas/sistemaLogin/paginaLogin.py`. Mapa geral em [[Páginas]]; o fluxo de sessão em [[Autenticação e sessão]].

## O que faz

Troca **usuário e senha** por uma chave de API (`POST /login`, ver [[Facede autenticacao]] no servidor) e avisa quem hospeda a página. Ela mesma não navega: emite o sinal `autenticado(chave, expira_em)`.

## Componentes

- **`PaginaLogin`** (`QWidget`): cartão de 340 px centralizado com título "Monitor KPI", campos de usuário (máx. 100 caracteres) e senha (máx. 200, mascarada), a caixa "Mostrar senha", o rótulo de erro e o botão **Entrar**.
- **`main()`**: monta a janela e decide a tela inicial (abaixo).

A página recebe o facede por parâmetro; sem ele usa `DIC.facede_autenticacao()`. Ela só chama `login`, nunca mexe na chave: quem grava a chave no adapter compartilhado (`DIC.api`) é o próprio facede.

## Funcionamento

### Ao abrir o app (`main`)

1. Chama `restaurar_sessao()`. Se há sessão guardada ainda válida, **vai direto ao menu**.
2. Senão, mostra o login numa janela de 480×520. Quando `autenticado` é emitido, a **mesma janela** troca o conteúdo para o [[Página de Menu|menu]] e passa para 1200×800.

O menu é importado só nessa hora (import tardio), então o login abre sem carregar as outras páginas.

### Ao clicar em Sair no menu

O `main()` também cuida do logout, porque é ele que sabe trocar a tela da janela: chama `facede_autenticacao().logout()`, `DIC.carrinho().esquecer()` e volta ao login (`ir_para_login`, janela de 480×520). Como o menu é descartado, o próximo login cria as páginas do zero.

### Ao clicar em Entrar (`entrar`)

1. Lê os campos, esconde o erro anterior.
2. Usuário ou senha vazios → "Informe usuário e senha." e para.
3. Desabilita o botão ("Entrando...") e põe o cursor de espera.
4. Chama `facede.login(nome, senha)`.
5. Ao terminar (qualquer resultado): restaura botão e cursor, e **limpa o campo da senha**.

| Resultado | O que a tela mostra |
|---|---|
| Sessão devolvida | emite `autenticado(chave, expira_em)` |
| `None` (401) | "Usuário ou senha inválidos." e foco na senha |
| `ApiError` sem `status_code` (rede, timeout) | "Não foi possível conectar ao servidor." |
| Outro `ApiError` | o `detalhe` da API (por exemplo, usuário ainda não validado) |

### Teclado

Enter no usuário passa o foco para a senha; Enter na senha equivale a clicar em Entrar.
