"""Tratador central de erro, T11.

Substitui os blocos try repetidos nos handlers. A guarda de HTTPException é
obrigatória: sem ela o tratador registrado para Exception também casaria com
as exceções de HTTP do roteamento, e um caminho inexistente passaria a
devolver 500 em vez de 404.
"""
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
        # Mensagem fixa, como faziam os blocos individuais do codigo original.
        # `str(exc)` devolvia ao cliente o texto cru da excecao: com o driver
        # SQL isso inclui a consulta e a lista de colunas de `users`. O detalhe
        # continua no registro de log acima, que e o lugar dele.
        return envelope.fail("Erro interno", 500)
