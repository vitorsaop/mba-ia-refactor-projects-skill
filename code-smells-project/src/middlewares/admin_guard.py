"""Guarda das operações administrativas, F02, T16 opção B.

Sem `ADMIN_TOKEN` definido, nenhuma requisição passa.
"""
import hmac
from functools import wraps

from flask import request

from src.config import settings
from src.controllers import envelope

CABECALHO = "X-Admin-Token"


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        enviado = request.headers.get(CABECALHO, "")
        # Comparação em bytes: `compare_digest` sobre texto levanta TypeError
        # quando o valor tem caractere fora de ASCII.
        if not settings.ADMIN_TOKEN or not hmac.compare_digest(
                enviado.encode("utf-8"), settings.ADMIN_TOKEN.encode("utf-8")):
            return envelope.falha("Não autorizado", 401)
        return view(*args, **kwargs)
    return wrapper
