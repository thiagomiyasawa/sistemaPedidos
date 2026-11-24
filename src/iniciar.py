"""Sobe o servidor (API) e o cliente (janela Qt) juntos.

Uso: `uv run monitorkpi-tudo`. Ao fechar a janela, o servidor é encerrado.
"""

import subprocess
import sys
import time

import httpx

HOST = "127.0.0.1"
PORTA = 8000


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
            "--host",
            HOST,
            "--port",
            str(PORTA),
        ]
    )
    try:
        if not _aguardar_servidor(servidor):
            raise SystemExit("Servidor não iniciou.")
        # Descomente apenas uma das páginas por vez.
        # from monitorkpi.paginas.paginasPedidos.paginaPedidosGeral.paginaGeral import main as cliente
        from client.monitorkpi.paginas.paginasPedidos.paginaPedidosObra.paginaObra import (
            main as cliente,
        )

        cliente()
    finally:
        servidor.terminate()
        try:
            servidor.wait(timeout=5)
        except subprocess.TimeoutExpired:
            servidor.kill()


if __name__ == "__main__":
    main()
