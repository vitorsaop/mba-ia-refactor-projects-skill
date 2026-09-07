"""Operações administrativas.

`executar` foi removida com a rota `POST /admin/query`, F03: a função entregava
o corpo da requisição a `conn.execute` sem validação.
"""
from src.config.database import get_connection


def reset():
    with get_connection() as conn:
        conn.execute("DELETE FROM itens_pedido")
        conn.execute("DELETE FROM pedidos")
        conn.execute("DELETE FROM produtos")
        conn.execute("DELETE FROM usuarios")
    return True
