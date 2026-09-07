import os
import secrets

# Categoria A (T2): valor não secreto, o literal atual vira o padrão.
DB_PATH = os.getenv("DB_PATH", "loja.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT = int(os.getenv("PORT", "5000"))
# F07, item [6] do portão: lista restritiva como padrão. Vazia significa
# nenhuma origem cruzada permitida.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

# F02, categoria C: segredo sem valor padrão. Ausente, a guarda recusa.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

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

# F15: valores que a resposta de saúde devolvia como literal no handler.
VERSAO = os.getenv("VERSAO", "1.0.0")
AMBIENTE = os.getenv("AMBIENTE", "producao")

# F01: derivação de senha, T17. Biblioteca padrão, nenhuma dependência nova.
SENHA_ALGORITMO = "sha256"
SENHA_ITERACOES = 240000
SENHA_TAMANHO_SAL = 16
