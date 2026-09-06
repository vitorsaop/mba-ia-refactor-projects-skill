import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register(app):
    @app.errorhandler(Exception)
    def handle(exc):
        if isinstance(exc, HTTPException):
            return exc
        logger.exception("erro não tratado")
        return jsonify({"erro": str(exc)}), 500
