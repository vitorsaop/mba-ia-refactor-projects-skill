"""Operações administrativas.

`executar_query`, que atendia `POST /admin/query`, foi removida junto com a
rota, F03. A função entregava a chave `sql` do corpo da requisição a
`conn.execute` sem validação e sem autenticação.
"""
import logging

from src.controllers import envelope
from src.models import admin_model

logger = logging.getLogger(__name__)


def reset_database():
    admin_model.reset()
    logger.warning("BANCO DE DADOS RESETADO")
    return envelope.ok(None, 200, mensagem="Banco de dados resetado")
