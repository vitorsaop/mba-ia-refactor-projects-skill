"""Guarda das operações destrutivas, T16 opção B.

F08, item [3] do portão: os três endpoints de remoção não verificavam
identidade nem permissão. A opção recomendada por gatilho C4 é proteger, não
remover, porque a operação tem uso operacional legítimo.

Sem `ADMIN_TOKEN` definido, nenhuma requisição passa.
"""
import hmac
from functools import wraps

from flask import request

from src.controllers import envelope

from src.config import settings

HEADER = "X-Admin-Token"


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        sent = request.headers.get(HEADER, "")
        # Comparar em bytes. `compare_digest` sobre texto levanta TypeError
        # quando o valor tem caractere fora de ASCII, e a guarda devolvia 500
        # em vez de 401 para um token malformado.
        if not settings.ADMIN_TOKEN or not hmac.compare_digest(
                sent.encode("utf-8"), settings.ADMIN_TOKEN.encode("utf-8")):
            return envelope.fail("Não autorizado", 401)
        return view(*args, **kwargs)
    return wrapper
