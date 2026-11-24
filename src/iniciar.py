"""Sobe o servidor (API) e o cliente (janela Qt) juntos.

O cliente abre pelo login (`client.paginas.sistemaLogin.paginaLogin`): com sessão guardada
ainda válida vai direto ao menu; senão pede usuário e senha e então abre o menu.

Uso: `.venv/Scripts/python.exe src/iniciar.py`. Ao fechar a janela, o servidor é encerrado.
"""

import subprocess
import sys
import time
from pathlib import Path

import httpx

HOST = "127.0.0.1"
PORTA = 8000
SRC = Path(__file__).resolve().parent  # pasta `src`: onde estão `bancoDadosSQL` e `client`


def _aguardar_servidor(proc: subprocess.Popen, timeout: float = 20.0) -> bool:
    """Espera a porta do servidor responder.

    Args:
        proc: processo do servidor, para detectar saída precoce.
        timeout: tempo máximo de espera em segundos.

    Returns:
        True se o servidor respondeu; False se caiu ou estourou o tempo.
    """
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        if proc.poll() is not None:
            return False
        try:
            httpx.get(f"http://{HOST}:{PORTA}/", timeout=1.0)
            return True  # qualquer resposta HTTP indica que está no ar
        except httpx.HTTPError:
            time.sleep(0.3)
    return False


def main() -> None:
    """Inicia o servidor em subprocesso e abre o cliente; encerra ambos ao final.

    Returns:
        None.
    """
    servidor = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "bancoDadosSQL.APIGateway:app",
            "--app-dir",
            str(SRC),
            "--host",
            HOST,
            "--port",
            str(PORTA),
        ]
    )
    try:
        if not _aguardar_servidor(servidor):
            raise SystemExit("Servidor não iniciou.")
        if str(SRC) not in sys.path:
            sys.path.insert(0, str(SRC))
        from client.paginas.sistemaLogin.paginaLogin import main as cliente

        cliente()
    finally:
        servidor.terminate()
        try:
            servidor.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor.kill()


if __name__ == "__main__":
    main()
