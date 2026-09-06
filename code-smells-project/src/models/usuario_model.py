from src.config.database import get_connection

CAMPOS = ("id", "nome", "email", "senha", "tipo", "criado_em")


def _to_dict(row):
    # Inclui "senha": achado C6/CRITICAL da auditoria (contract-breaking).
    # Não autorizado no portão da Fase 2 — preservado até autorização futura.
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
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha)
        ).fetchone()
    if row:
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None


def create(nome, email, senha, tipo="cliente"):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha, tipo),
        )
        return cursor.lastrowid
