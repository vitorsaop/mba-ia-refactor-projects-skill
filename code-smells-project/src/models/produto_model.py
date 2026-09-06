from src.config.database import get_connection

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row):
    return {campo: row[campo] for campo in CAMPOS}


def get_all():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM produtos").fetchall()
    return [_to_dict(row) for row in rows]


def get_by_id(produto_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _to_dict(row) if row else None


def create(nome, descricao, preco, estoque, categoria):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        return cursor.lastrowid


def update(produto_id, nome, descricao, preco, estoque, categoria):
    with get_connection() as conn:
        conn.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
            "categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
    return True


def delete(produto_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    return True


def search(termo, categoria=None, preco_min=None, preco_max=None):
    clausulas = ["1=1"]
    parametros = []
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        parametros.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        clausulas.append("categoria = ?")
        parametros.append(categoria)
    if preco_min:
        clausulas.append("preco >= ?")
        parametros.append(preco_min)
    if preco_max:
        clausulas.append("preco <= ?")
        parametros.append(preco_max)

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM produtos WHERE " + " AND ".join(clausulas), parametros
        ).fetchall()
    return [_to_dict(row) for row in rows]
