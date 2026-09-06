from src.config.database import get_connection


def reset():
    with get_connection() as conn:
        conn.execute("DELETE FROM itens_pedido")
        conn.execute("DELETE FROM pedidos")
        conn.execute("DELETE FROM produtos")
        conn.execute("DELETE FROM usuarios")
    return True


def executar(query):
    with get_connection() as conn:
        cursor = conn.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            return {"select": True, "dados": [dict(row) for row in rows]}
        return {"select": False}
