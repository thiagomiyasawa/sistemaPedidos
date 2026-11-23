"""Facade de autenticação por chave de API guardada no banco.

Consulta a tabela `chavesAPI` (chave, user_id, DateTime_exp). A chave só é aceita
se existir e `DateTime_exp` for posterior ao instante atual (UTC, como o
`CURRENT_TIMESTAMP` do SQLite). Validade nula é tratada como inválida.

Login: confere nome e senha na tabela `usuario` (senha guardada como hash scrypt,
ver `hash_senha`) e grava uma nova chave aleatória em `chavesAPI`.

Uso:
    with DIC.db() as db:
        f = FacedeAutenticacao(db)
        chave, expira = f.login("ana", "segredo")
        ok = f.autenticar(chave)
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from ..dbAdapterInterface import dbAdapterInterface
from .interfaces.facedeAutenticacaoInterface import Identidade, facedeAutenticacaoInterface

_FORMATO_DATA = "%Y-%m-%d %H:%M:%S"  # como `datetime('now')` do SQLite (UTC, texto)
VALIDADE_PADRAO = timedelta(hours=8)
CARGO_PENDENTE = "pendente"  # `usuario.cargo` é NOT NULL: o validador define o cargo real
_SCRYPT = {"n": 2**14, "r": 8, "p": 1}


def hash_senha(senha: str) -> str:
    """Gera o hash para guardar em `usuario.senha` (scrypt com sal aleatório).

    Args:
        senha: senha em texto puro.

    Returns:
        str: texto no formato `scrypt$<sal hex>$<hash hex>`.
    """
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(senha.encode(), salt=sal, **_SCRYPT)
    return f"scrypt${sal.hex()}${h.hex()}"


def _confere_senha(senha: str, guardado: str | None) -> bool:
    """Compara a senha com o hash guardado, em tempo constante.

    Args:
        senha: senha em texto puro.
        guardado: valor de `usuario.senha` (formato de `hash_senha`), ou None.

    Returns:
        bool: True se confere; False se difere ou o formato for inválido.
    """
    try:
        esquema, sal, esperado = (guardado or "").split("$")
        if esquema != "scrypt":
            return False
        h = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal), **_SCRYPT)
        return hmac.compare_digest(h, bytes.fromhex(esperado))
    except ValueError:
        return False


# Hash descartável: usado quando o usuário não existe, para o tempo de resposta
# não revelar se o nome é válido.
_HASH_FALSO = hash_senha(secrets.token_hex(8))


class FacedeAutenticacao(facedeAutenticacaoInterface):
    """Valida chaves de API e emite chaves no login, usando `chavesAPI` e `usuario`.

    Attributes:
        db: adapter de banco usado para consultar as tabelas.
        validade: duração das chaves emitidas no login.
    """

    def __init__(self, db: dbAdapterInterface, validade: timedelta = VALIDADE_PADRAO) -> None:
        """Inicializa o facade com o adapter de banco.

        Args:
            db: adapter que satisfaz `dbAdapterInterface`.
            validade: duração das chaves emitidas no login.
        """
        self.db = db
        self.validade = validade

    def registrar(self, nome: str, senha: str) -> int | None:
        """Cria um usuário novo, inativo (`ativo = 0`) até alguém validar o registro.

        O cargo inicial é `CARGO_PENDENTE` (coluna NOT NULL). O nome é verificado
        sem diferenciar maiúsculas no mesmo INSERT (além do UNIQUE da tabela); o
        id vem da chave primária da tabela.

        Args:
            nome: nome do usuário (único, sem diferenciar maiúsculas).
            senha: senha em texto puro (guardada apenas como hash).

        Returns:
            int | None: id do usuário criado; None se o nome já estiver em uso.
        """
        cur = self.db.execute(
            "INSERT INTO usuario (nome, senha, cargo, ativo) "
            "SELECT ?, ?, ?, 0 "
            "WHERE NOT EXISTS (SELECT 1 FROM usuario WHERE nome = ? COLLATE NOCASE)",
            (nome, hash_senha(senha), CARGO_PENDENTE, nome),
        )
        if cur.rowcount == 0:
            return None
        return self.db.fetch_one("SELECT id FROM usuario WHERE nome = ?", (nome,))["id"]

    def login(self, nome: str, senha: str) -> tuple[str, datetime] | None:
        """Valida usuário e senha e emite uma nova chave de API.

        Args:
            nome: nome do usuário.
            senha: senha em texto puro.

        Returns:
            tuple[str, datetime] | None: (chave, vencimento em UTC) da chave
            gravada em `chavesAPI`; None se usuário inexistente, inativo
            (`usuario.ativo` diferente de 1) ou senha incorreta.
        """
        usuario = self.db.fetch_one("SELECT id, senha, ativo FROM usuario WHERE nome = ?", (nome,))
        senha_ok = _confere_senha(senha, usuario["senha"] if usuario else _HASH_FALSO)
        # Usuário inativo é recusado só depois de conferir a senha, com a mesma
        # resposta de credencial inválida (não revela que a conta existe).
        if usuario is None or not senha_ok or usuario["ativo"] != 1:
            return None
        chave = secrets.token_urlsafe(32)
        expira = (datetime.now(UTC) + self.validade).replace(microsecond=0)
        self.db.execute(
            "INSERT INTO chavesAPI (chave, user_id, DateTime_exp) VALUES (?, ?, ?)",
            (chave, usuario["id"], expira.strftime(_FORMATO_DATA)),
        )
        return chave, expira

    def autenticar(self, chave: str | None) -> Identidade | None:
        """Verifica se a chave existe, não está vencida e é de usuário ativo.

        Efeito colateral: se a chave existir mas estiver vencida, ela é apagada
        da tabela `chavesAPI`.

        Args:
            chave: chave recebida na requisição, ou None se ausente.

        Returns:
            Identidade | None: dono da chave; None se ausente, inexistente,
            vencida, sem validade ou de usuário inativo.
        """
        if not chave:
            return None
        # Uma consulta só: `valida` é 1 (futuro), 0 (vencida) ou NULL (sem validade).
        linha = self.db.fetch_one(
            "SELECT c.DateTime_exp > datetime('now') AS valida, u.id AS user_id, "
            "u.cargo AS cargo, u.ativo AS ativo "
            "FROM chavesAPI c JOIN usuario u ON u.id = c.user_id WHERE c.chave = ?",
            (chave,),
        )
        if linha is None:
            return None
        if linha["valida"] == 0:  # vencida: apaga (só aqui há escrita)
            self.db.execute("DELETE FROM chavesAPI WHERE chave = ?", (chave,))
            return None
        if linha["valida"] != 1 or linha["ativo"] != 1:
            return None
        return Identidade(user_id=linha["user_id"], cargo=linha["cargo"])
