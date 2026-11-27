Como o [[Cliente]] se identifica no servidor: login com nome e senha, chave de API guardada em arquivo, restauração da sessão na próxima abertura e logout. Do lado do servidor, ver [[Facede autenticacao]] e [[API Gateway]].

## Fluxo ao abrir o app

`paginaLogin.main()` decide a tela inicial:

1. `restaurar_sessao()` tem sucesso → vai **direto ao menu**.
2. Caso contrário → mostra o **login**; ao autenticar, a mesma janela troca para o menu.

Depois do login, a chave já está no adapter compartilhado (`DIC.api`), então as páginas do menu enviam `X-API-Key` sem nenhum passo extra.

## FacedeAutenticacaoAPI (`client/facedes/facedeAutenticacao.py`)

Implementa `facedeAutenticacaoInterface`. Recebe o adapter da API e o armazenamento da sessão (padrões: `AdapterAPI` e `SessaoArquivo`).

### login(nome, senha) -> Sessao | None

`POST /login`. Se aceito: chama `definir_api_key` no adapter e grava a sessão no armazenamento. Retorna `None` se a API responder 401 (usuário ou senha inválidos; usuário inativo recebe a mesma resposta). Outros erros sobem como `ApiError`. Se falhar só a gravação do arquivo (`OSError`), o login continua valendo e o problema vai para o log.

### restaurar_sessao() -> Sessao | None

Reaproveita a sessão guardada:

1. Sem arquivo ou com data ilegível → `None` (data ilegível também apaga o arquivo).
2. Vencida (a API devolve UTC) → apaga o arquivo e devolve `None`.
3. Senão, usa a chave e confirma com `GET /health`, que exige chave. Isso detecta chave revogada ou usuário desativado.
   - 401 → apaga a sessão.
   - API fora do ar → mantém o arquivo, mas **não** restaura (a chave é removida do adapter).

### logout() -> bool

Encerra a sessão. Chama `POST /logout` e, **aconteça o que acontecer**, esquece a sessão neste computador: remove a chave do adapter (`definir_api_key("")`) e apaga o arquivo da sessão.

- Devolve `True` se a API revogou a chave. Um 401 (chave já vencida ou revogada) também conta como sucesso.
- Devolve `False` se não foi possível avisar a API (rede, timeout, erro 5xx). O usuário sai do app mesmo assim, o problema vai para o log e a chave **continua valendo no servidor até vencer**.
- O servidor apaga a chave, e como o login reaproveita a chave vigente, o logout encerra a sessão em **todos os computadores** que a compartilham (ver [[Facede autenticacao]]).

### close() e with

Fecham o adapter.

## Sessao

`@dataclass(frozen=True)` com `chave` e `expira_em` (UTC, texto ISO 8601).

## Armazenamento da sessão

Contrato: `armazenamentoSessaoInterface` (`salvar`, `carregar`, `limpar`). Implementação: `SessaoArquivo` (`client/armazenamento/sessaoArquivo.py`).

- Arquivo JSON `{"chave": ..., "expira_em": ...}`. Local: `MONITORKPI_SESSAO_ARQUIVO`, senão `sessao.json` na raiz do projeto.
- **A chave fica em texto puro.** O arquivo é criado com permissão `0600` (só tem efeito real no Linux/macOS) e está no `.gitignore`.
- Escrita atômica: grava em `sessao.json.tmp` e substitui.
- `carregar()` devolve `None` se o arquivo não existe ou está inválido; `limpar()` apaga o arquivo.

## Logout na interface

O botão **Sair**, no pé da barra lateral do [[Página de Menu|menu]], emite o sinal `sair`. Quem trata é `main()` de [[Página de Login]]:

1. `facede_autenticacao().logout()`;
2. `DIC.carrinho().esquecer()`: descarta a cópia local do carrinho (sem tocar na API), para o próximo usuário não ver os itens do anterior;
3. troca a mesma janela de volta para o login (480×520).

O menu é descartado, então um novo login cria todas as páginas do zero. Na próxima abertura do app não há sessão guardada, então ele abre no login.
