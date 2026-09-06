from src.config.database import get_connection

SQL_ITENS = """
    SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
           p.nome AS produto_nome
    FROM itens_pedido ip
    LEFT JOIN produtos p ON p.id = ip.produto_id
    WHERE ip.pedido_id IN ({placeholders})
    ORDER BY ip.pedido_id, ip.id
"""


def _pedido_base(row):
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": [],
    }


def _itens_por_pedido(conn, pedido_ids):
    if not pedido_ids:
        return {}
    placeholders = ",".join("?" for _ in pedido_ids)
    linhas = conn.execute(SQL_ITENS.format(placeholders=placeholders), pedido_ids).fetchall()
    agrupado = {pid: [] for pid in pedido_ids}
    for linha in linhas:
        agrupado[linha["pedido_id"]].append({
            "produto_id": linha["produto_id"],
            "produto_nome": linha["produto_nome"] or "Desconhecido",
            "quantidade": linha["quantidade"],
            "preco_unitario": linha["preco_unitario"],
        })
    return agrupado


def _montar_pedidos(conn, rows):
    pedidos = [_pedido_base(row) for row in rows]
    itens_por_pedido = _itens_por_pedido(conn, [pedido["id"] for pedido in pedidos])
    for pedido in pedidos:
        pedido["itens"] = itens_por_pedido.get(pedido["id"], [])
    return pedidos


def get_by_usuario(usuario_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)
        ).fetchall()
        return _montar_pedidos(conn, rows)


def get_all():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM pedidos").fetchall()
        return _montar_pedidos(conn, rows)


def _produtos_por_id(conn, itens):
    produto_ids = [item["produto_id"] for item in itens]
    placeholders = ",".join("?" for _ in produto_ids)
    rows = conn.execute(
        f"SELECT * FROM produtos WHERE id IN ({placeholders})", produto_ids
    ).fetchall()
    return {row["id"]: row for row in rows}


def create(usuario_id, itens):
    with get_connection() as conn:
        produtos_por_id = _produtos_por_id(conn, itens)

        total = 0
        for item in itens:
            produto = produtos_por_id.get(item["produto_id"])
            if produto is None:
                return {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
            if produto["estoque"] < item["quantidade"]:
                return {"erro": "Estoque insuficiente para " + produto["nome"]}
            total = total + (produto["preco"] * item["quantidade"])

        cursor = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            preco = produtos_por_id[item["produto_id"]]["preco"]
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], preco),
            )
            conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )

        return {"pedido_id": pedido_id, "total": total}


def update_status(pedido_id, novo_status):
    with get_connection() as conn:
        conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    return True
