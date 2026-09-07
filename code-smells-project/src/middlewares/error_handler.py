import logging

from werkzeug.exceptions import HTTPException

from src.controllers import envelope

logger = logging.getLogger(__name__)


def register(app):
    @app.errorhandler(Exception)
    def handle(exc):
        if isinstance(exc, HTTPException):
            return exc
        logger.exception("erro não tratado")
        # F08: `str(exc)` devolvia ao cliente o comando SQL e a lista de
        # colunas da tabela. O detalhe fica no registro de log acima.
        return envelope.falha("Erro interno", 500)
