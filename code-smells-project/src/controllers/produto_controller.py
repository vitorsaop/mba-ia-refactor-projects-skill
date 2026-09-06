import logging

from flask import request, jsonify

from src.models import produto_model
from src.config.settings import CATEGORIAS_VALIDAS, NOME_PRODUTO_MIN_LENGTH, NOME_PRODUTO_MAX_LENGTH

logger = logging.getLogger(__name__)


def listar():
    produtos = produto_model.get_all()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar():
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    if "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    if "preco" not in dados:
        return jsonify({"erro": "Preço é obrigatório"}), 400
    if "estoque" not in dados:
        return jsonify({"erro": "Estoque é obrigatório"}), 400

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        return jsonify({"erro": "Preço não pode ser negativo"}), 400
    if estoque < 0:
        return jsonify({"erro": "Estoque não pode ser negativo"}), 400
    if len(nome) < NOME_PRODUTO_MIN_LENGTH:
        return jsonify({"erro": "Nome muito curto"}), 400
    if len(nome) > NOME_PRODUTO_MAX_LENGTH:
        return jsonify({"erro": "Nome muito longo"}), 400

    if categoria not in CATEGORIAS_VALIDAS:
        return jsonify({"erro": "Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS))}), 400

    produto_id = produto_model.create(nome, descricao, preco, estoque, categoria)
    logger.info("produto criado id=%s", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar(produto_id):
    dados = request.get_json()

    produto_existente = produto_model.get_by_id(produto_id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado"}), 404

    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    if "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    if "preco" not in dados:
        return jsonify({"erro": "Preço é obrigatório"}), 400
    if "estoque" not in dados:
        return jsonify({"erro": "Estoque é obrigatório"}), 400

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        return jsonify({"erro": "Preço não pode ser negativo"}), 400
    if estoque < 0:
        return jsonify({"erro": "Estoque não pode ser negativo"}), 400

    produto_model.update(produto_id, nome, descricao, preco, estoque, categoria)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    produto_model.delete(produto_id)
    logger.info("produto deletado id=%s", produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_varios():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    resultados = produto_model.search(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
