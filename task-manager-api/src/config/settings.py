"""Configuração da aplicação: leitura de ambiente e constantes nomeadas.

Valor não secreto mantém como padrão o literal que o projeto já tinha, para
que o comando de boot documentado continue funcionando sem nenhuma variável
definida. Segredo não mantém literal algum.
"""
import os
import secrets

from dotenv import load_dotenv

# `python-dotenv` já é dependência declarada em requirements.txt. Sem esta
# chamada, o `.env` que `.env.example` manda criar nunca seria lido.
load_dotenv()

# --- Categoria A, valores não secretos. O literal atual vira o padrão. -------
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///tasks.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Categoria B, segredo que não assina nada neste projeto. -----------------
# Verificado antes de aplicar: o projeto não usa session, flash, cookie
# assinado nem token assinado. Uma chave distinta por boot não altera nada
# observável, portanto o literal sai do código e não deixa padrão.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)

# --- Categoria C, segredo exigido no momento do uso. -------------------------
# Sem valor padrão. Ausente a variável, a guarda administrativa recusa.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# --- Origem cruzada. ---------------------------------------------------------
# Item [4] do portão da Fase 2, autorizado: lista restritiva como padrão.
# Vazia significa nenhuma origem cruzada permitida. Definir CORS_ORIGINS
# libera exatamente as origens listadas, separadas por vírgula.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

# --- Regras de negócio. Valores idênticos aos do código original. ------------
VALID_TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
TERMINAL_TASK_STATUSES = ("done", "cancelled")
DEFAULT_TASK_STATUS = "pending"
VALID_USER_ROLES = ("user", "admin", "manager")
DEFAULT_USER_ROLE = "user"

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
MIN_PASSWORD_LENGTH = 4

DEFAULT_COLOR = "#000000"
COLOR_LENGTH = 7
COLOR_PREFIX = "#"

DUE_DATE_FORMAT = "%Y-%m-%d"
EMAIL_PATTERN = r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
TAG_SEPARATOR = ","

# Faixa de atividade recente do relatório e limite de prioridade alta.
RECENT_ACTIVITY_DAYS = 7
HIGH_PRIORITY_MAX = 2

# Prioridade numérica para o nome de negócio usado nas chaves de resposta.
PRIORITY_LABELS = (
    (1, "critical"),
    (2, "high"),
    (3, "medium"),
    (4, "low"),
    (5, "minimal"),
)

# Prefixo do token devolvido pelo login. Valor idêntico ao original.
TOKEN_PREFIX = "fake-jwt-token-"

# Derivação de senha, T17. Biblioteca padrão, nenhuma dependência nova.
PASSWORD_ALGORITHM = "sha256"
PASSWORD_ITERATIONS = 240000
PASSWORD_SALT_BYTES = 16
