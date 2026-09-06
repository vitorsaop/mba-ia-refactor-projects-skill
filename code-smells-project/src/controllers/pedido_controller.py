import logging

from flask import request, jsonify

from src.models import pedido_model
from src.config.settings import STATUS_PEDIDO_VALIDOS

logger = logging.getLogger(__name__)


def criar():
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens or len(itens) == 0:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    resultado = pedido_model.create(usuario_id, itens)

    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    logger.info("pedido criado id=%s usuario_id=%s", resultado["pedido_id"], usuario_id)
    logger.info("notificacao simulada (email) para pedido %s", resultado["pedido_id"])
    logger.info("notificacao simulada (sms) para pedido %s", resultado["pedido_id"])
    logger.info("notificacao simulada (push) para pedido %s", resultado["pedido_id"])

    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso"
    }), 201


def listar_por_usuario(usuario_id):
    pedidos = pedido_model.get_by_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos():
    pedidos = pedido_model.get_all()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status(pedido_id):
    dados = request.get_json()
    novo_status = dados.get("status", "")

    if novo_status not in STATUS_PEDIDO_VALIDOS:
        return jsonify({"erro": "Status inválido"}), 400

    pedido_model.update_status(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("pedido %s aprovado, preparar envio", pedido_id)
    if novo_status == "cancelado":
        logger.info("pedido %s cancelado, devolver estoque", pedido_id)

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
