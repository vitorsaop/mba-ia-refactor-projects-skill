"""Montagem do corpo de resposta.

T22, item [8] do portão da Fase 2. Todo endpoint passa a devolver o mesmo
envelope: `dados` e `sucesso` no caminho de sucesso, `erro` e `sucesso` no
caminho de erro.

Fica na camada de controller porque a tabela `contém / não contém` atribui a
ela a montagem da resposta.
"""
from flask import jsonify


def ok(payload, status=200):
    return jsonify({"dados": payload, "sucesso": True}), status


def fail(message, status):
    return jsonify({"erro": message, "sucesso": False}), status
