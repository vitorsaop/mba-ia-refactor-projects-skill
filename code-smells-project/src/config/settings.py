import os
import secrets

# Categoria A (T2): valor não secreto, o literal atual vira o padrão.
DB_PATH = os.getenv("DB_PATH", "loja.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT = int(os.getenv("PORT", "5000"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

# Categoria B (T2): segredo sem verificação externa. O projeto não usa
# session, flash nem assinatura, portanto uma chave distinta por boot não
# altera nenhum comportamento observável.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)

# T13: faixas de desconto do relatório de vendas, valores idênticos aos da
# implementação original, ordenadas do maior limite para o menor.
FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
STATUS_PEDIDO_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

NOME_PRODUTO_MIN_LENGTH = 2
NOME_PRODUTO_MAX_LENGTH = 200
