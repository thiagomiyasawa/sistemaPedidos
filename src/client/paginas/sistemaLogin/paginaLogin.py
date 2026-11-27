"""Página de login (PySide6): troca usuário e senha por uma chave de API (`POST /login`).

Ao autenticar, emite o sinal `autenticado(chave, expira_em)`; quem hospeda a página decide o
que fazer em seguida. O acesso à API é feito só pelo facade de autenticação (`DIC`), que também
passa o adapter compartilhado a enviar a chave nas requisições seguintes.
Execução:
    .venv\\Scripts\\python.exe "src/client/paginas/sistemaLogin/paginaLogin.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite rodar o arquivo diretamente: coloca `src` no path (antes dos imports do projeto).
_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from PySide6.QtCore import Qt, Signal  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QCheckBox,
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from client.adapters.interfaces.adapterAPIInterface import ApiError  # noqa: E402
from client.DIC import DIC  # noqa: E402
from client.facedes.interfaces.facedeAutenticacaoInterface import (  # noqa: E402
    facedeAutenticacaoInterface,
)

ESTILO_LOGIN = """
QWidget { font-size: 10pt; }
#cartaoLogin { background: palette(base); border: 1px solid palette(mid); border-radius: 10px; }
#tituloLogin { font-size: 18pt; font-weight: 700; }
#subtituloLogin { color: palette(placeholder-text); }
#rotuloCampo { font-size: 8pt; color: palette(placeholder-text); }
QLineEdit { padding: 7px 9px; border: 1px solid palette(mid); border-radius: 6px; }
QLineEdit:focus { border: 1px solid palette(highlight); }
#botaoEntrar { padding: 9px; font-weight: 600; border-radius: 6px;
               background: palette(highlight); color: palette(highlighted-text); }
#botaoEntrar:disabled { background: palette(mid); }
#erroLogin { color: #c0392b; }
"""


class PaginaLogin(QWidget):
    """Formulário de login centralizado numa janela.

    Attributes:
        autenticado: Sinal `(chave, expira_em)` emitido após login bem-sucedido.
        campo_usuario: Campo de texto do nome do usuário.
        campo_senha: Campo de texto da senha (mascarado).
        rotulo_erro: Rótulo que exibe a mensagem de falha.
    """

    autenticado = Signal(str, str)

    def __init__(self, facede: facedeAutenticacaoInterface | None = None) -> None:
        """Monta o cartão de login.

        Args:
            facede: facade de autenticação; se None usa `DIC.facede_autenticacao()`.

        Returns:
            None.
        """
        super().__init__()
        self._facede = facede or DIC.facede_autenticacao()
        self.setStyleSheet(ESTILO_LOGIN)

        titulo = QLabel("Monitor KPI")
        titulo.setObjectName("tituloLogin")
        titulo.setAlignment(Qt.AlignCenter)
        sub = QLabel("Entre com seu usuário e senha")
        sub.setObjectName("subtituloLogin")
        sub.setAlignment(Qt.AlignCenter)

        self.campo_usuario = QLineEdit()
        self.campo_usuario.setPlaceholderText("Usuário")
        self.campo_usuario.setMaxLength(100)
        self.campo_senha = QLineEdit()
        self.campo_senha.setPlaceholderText("Senha")
        self.campo_senha.setMaxLength(200)
        self.campo_senha.setEchoMode(QLineEdit.Password)

        mostrar = QCheckBox("Mostrar senha")
        mostrar.toggled.connect(
            lambda v: self.campo_senha.setEchoMode(
                QLineEdit.Normal if v else QLineEdit.Password
            )
        )

        self.rotulo_erro = QLabel("")
        self.rotulo_erro.setObjectName("erroLogin")
        self.rotulo_erro.setWordWrap(True)
        self.rotulo_erro.setAlignment(Qt.AlignCenter)
        self.rotulo_erro.hide()

        self.botao = QPushButton("Entrar")
        self.botao.setObjectName("botaoEntrar")
        self.botao.setCursor(Qt.PointingHandCursor)
        self.botao.setDefault(True)
        self.botao.clicked.connect(self.entrar)
        self.campo_usuario.returnPressed.connect(self.campo_senha.setFocus)
        self.campo_senha.returnPressed.connect(self.entrar)

        cartao = QFrame()
        cartao.setObjectName("cartaoLogin")
        cartao.setFixedWidth(340)
        lay = QVBoxLayout(cartao)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(10)
        lay.addWidget(titulo)
        lay.addWidget(sub)
        lay.addSpacing(8)
        lay.addWidget(self._com_rotulo("Usuário", self.campo_usuario))
        lay.addWidget(self._com_rotulo("Senha", self.campo_senha))
        lay.addWidget(mostrar)
        lay.addWidget(self.rotulo_erro)
        lay.addWidget(self.botao)

        raiz = QVBoxLayout(self)
        raiz.addStretch(1)
        raiz.addWidget(cartao, 0, Qt.AlignHCenter)
        raiz.addStretch(1)

        self.campo_usuario.setFocus()

    @staticmethod
    def _com_rotulo(texto: str, campo: QWidget) -> QWidget:
        """Põe um rótulo pequeno sobre o campo.

        Args:
            texto: Texto do rótulo.
            campo: Widget de entrada.

        Returns:
            Contêiner (rótulo + campo).
        """
        caixa = QWidget()
        box = QVBoxLayout(caixa)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        lbl = QLabel(texto)
        lbl.setObjectName("rotuloCampo")
        box.addWidget(lbl)
        box.addWidget(campo)
        return caixa

    def _mostrar_erro(self, mensagem: str) -> None:
        """Exibe a mensagem de erro sob os campos.

        Args:
            mensagem: Texto a exibir.

        Returns:
            None.
        """
        self.rotulo_erro.setText(mensagem)
        self.rotulo_erro.show()

    def entrar(self) -> None:
        """Valida os campos, chama `POST /login` e emite `autenticado` em caso de sucesso.

        Erros (campos vazios, credenciais inválidas, API fora do ar) aparecem no `rotulo_erro`.

        Returns:
            None.
        """
        nome = self.campo_usuario.text().strip()
        senha = self.campo_senha.text()
        self.rotulo_erro.hide()
        if not nome or not senha:
            self._mostrar_erro("Informe usuário e senha.")
            return

        self.botao.setEnabled(False)
        self.botao.setText("Entrando...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            sessao = self._facede.login(nome, senha)
        except ApiError as e:
            if e.status_code is None:
                self._mostrar_erro("Não foi possível conectar ao servidor.")
            else:
                self._mostrar_erro(str(e.detalhe or e))
            self.campo_senha.clear()
            self.campo_senha.setFocus()
            return
        finally:
            QApplication.restoreOverrideCursor()
            self.botao.setEnabled(True)
            self.botao.setText("Entrar")

        self.campo_senha.clear()
        if sessao is None:
            self._mostrar_erro("Usuário ou senha inválidos.")
            self.campo_senha.setFocus()
            return
        self.autenticado.emit(sessao.chave, sessao.expira_em)


def main() -> None:
    """Abre o app: com sessão guardada ainda válida vai direto ao menu; senão mostra o login.

    Em caso de login bem-sucedido, redireciona a mesma janela para o menu. O facade de autenticação já grava a chave no adapter compartilhado (`DIC.api`), então as
    páginas do menu passam a enviá-la sem nenhum passo extra aqui.

    O botão "Sair" do menu faz o logout (revoga a chave, apaga a sessão guardada e esquece o
    carrinho local) e devolve a mesma janela ao login. Como o menu é descartado, um novo login
    cria as páginas do zero, sem dados do usuário anterior.

    Returns:
        None. Bloqueia até a janela ser fechada.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    janela = QMainWindow()
    janela.resize(480, 520)

    def ir_para_menu(*_sessao: str) -> None:
        from client.paginas.sistemaMenu.paginaMenu import PaginaMenu

        menu = PaginaMenu()
        menu.sair.connect(sair)
        janela.setWindowTitle("Monitor KPI")
        janela.resize(1200, 800)
        janela.setCentralWidget(menu)  # o Qt descarta a página anterior

    def ir_para_login() -> None:
        pagina = PaginaLogin()
        pagina.autenticado.connect(ir_para_menu)
        janela.setWindowTitle("Monitor KPI - Login")
        janela.resize(480, 520)
        janela.setCentralWidget(pagina)

    def sair() -> None:
        DIC.facede_autenticacao().logout()  # sempre limpa o lado local; falha da API só vai ao log
        DIC.carrinho().esquecer()
        ir_para_login()

    if DIC.facede_autenticacao().restaurar_sessao() is not None:
        ir_para_menu()
    else:
        ir_para_login()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
