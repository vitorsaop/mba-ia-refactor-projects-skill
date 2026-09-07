"""Modelo de usuário: dados, derivação de senha e serialização pública."""
import hashlib
import hmac
import os

from src.config import settings
from src.config.database import get_connection

# F06: a chave `senha` saiu da serialização pública. A tupla lista apenas o
# que os dois endpoints de leitura devolvem.
CAMPOS = ("id", "nome", "email", "tipo", "criado_em")


def hash_senha(senha):
    """Deriva a senha com sal por usuário, F01, T17. Biblioteca padrão."""
    sal = os.urandom(settings.SENHA_TAMANHO_SAL)
    digest = hashlib.pbkdf2_hmac(
        settings.SENHA_ALGORITMO, senha.encode(), sal, settings.SENHA_ITERACOES)
    return (f"pbkdf2_{settings.SENHA_ALGORITMO}${settings.SENHA_ITERACOES}"
            f"${sal.hex()}${digest.hex()}")


def verifica_senha(senha, armazenado):
    """Compara em tempo constante. Valor em texto puro não valida."""
    if not armazenado:
        return False
    try:
        prefixo, iteracoes, sal_hex, digest_hex = armazenado.split("$")
    except ValueError:
        return False
    if not prefixo.startswith("pbkdf2_"):
        return False
    try:
        digest = hashlib.pbkdf2_hmac(
            prefixo[len("pbkdf2_"):], senha.encode(),
            bytes.fromhex(sal_hex), int(iteracoes))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def _to_dict(row):
    return {campo: row[campo] for campo in CAMPOS}


def get_all():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def get_by_id(usuario_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def login(email, senha):
    """F01: a comparação saiu da cláusula WHERE e passou a ser de tempo
    constante sobre o digest derivado."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row and verifica_senha(senha, row["senha"]):
        return {"id": row["id"], "nome": row["nome"],
                "email": row["email"], "tipo": row["tipo"]}
    return None


def create(nome, email, senha, tipo="cliente"):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, hash_senha(senha), tipo))
        return cursor.lastrowid
