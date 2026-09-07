"""Montagem do corpo de resposta.

F14, item [11] do portão, cobre exatamente quatro endpoints: `GET /`,
`GET /health`, `PUT /produtos/<id>` e `DELETE /produtos/<id>`. Fora deles o
corpo permanece idêntico ao da linha de base, inclusive a presença ou ausência
da chave `sucesso` nas respostas de erro, que na linha de base era
inconsistente entre endpoints.
"""
from flask import jsonify


def ok(dados, status=200, mensagem=None, extras=None):
    corpo = {"dados": dados, "sucesso": True}
    if mensagem is not None:
        corpo["mensagem"] = mensagem
    if extras:
        corpo.update(extras)
    return jsonify(corpo), status


def ok_sem_dados(status=200, mensagem=None):
    """Sucesso sem a chave `dados`, forma que a linha de base usa em
    `PUT /pedidos/<id>/status`."""
    corpo = {"sucesso": True}
    if mensagem is not None:
        corpo["mensagem"] = mensagem
    return jsonify(corpo), status


def falha(erro, status, com_sucesso=False):
    """A chave `sucesso` só entra onde a linha de base já a devolvia."""
    corpo = {"erro": erro}
    if com_sucesso:
        corpo["sucesso"] = False
    return jsonify(corpo), status
