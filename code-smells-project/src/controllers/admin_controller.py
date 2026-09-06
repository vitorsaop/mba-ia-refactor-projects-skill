import logging

from flask import request, jsonify

from src.models import admin_model

logger = logging.getLogger(__name__)


def reset_database():
    admin_model.reset()
    logger.warning("BANCO DE DADOS RESETADO")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = request.get_json()
    query = dados.get("sql", "")
    if not query:
        return jsonify({"erro": "Query não informada"}), 400

    resultado = admin_model.executar(query)
    if resultado["select"]:
        return jsonify({"dados": resultado["dados"], "sucesso": True}), 200
    return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
