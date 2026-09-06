import logging

from flask import request, jsonify

from src.models import usuario_model

logger = logging.getLogger(__name__)


def listar():
    usuarios = usuario_model.get_all()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar(usuario_id):
    usuario = usuario_model.get_by_id(usuario_id)
    if usuario:
        return jsonify({"dados": usuario, "sucesso": True}), 200
    return jsonify({"erro": "Usuário não encontrado"}), 404


def criar():
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    usuario_id = usuario_model.create(nome, email, senha)
    logger.info("usuario criado email=%s", email)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = request.get_json()
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = usuario_model.login(email, senha)
    if usuario:
        logger.info("login bem-sucedido email=%s", email)
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

    logger.info("login falhou email=%s", email)
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
