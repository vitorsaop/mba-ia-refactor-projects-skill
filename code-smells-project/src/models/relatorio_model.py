from src.config.database import get_connection
from src.config.settings import FAIXAS_DESCONTO


def _calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def vendas():
    with get_connection() as conn:
        total_pedidos = conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        faturamento = conn.execute("SELECT SUM(total) FROM pedidos").fetchone()[0]
        if faturamento is None:
            faturamento = 0
        pendentes = conn.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'"
        ).fetchone()[0]
        aprovados = conn.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'"
        ).fetchone()[0]
        cancelados = conn.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'"
        ).fetchone()[0]

    desconto = _calcular_desconto(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


def contagens_saude():
    with get_connection() as conn:
        conn.execute("SELECT 1")
        produtos = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        usuarios = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        pedidos = conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    return {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos}
