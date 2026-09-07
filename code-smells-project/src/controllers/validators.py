"""Validação de formato de entrada, F10 e F13."""
from flask import request


def corpo_objeto():
    """Corpo da requisição quando for objeto JSON, `None` caso contrário.

    F10: `if not dados` aprova qualquer valor verdadeiro, então um corpo JSON
    válido que não seja objeto atravessava a guarda e quebrava no `.get`
    seguinte. Três handlers nem tinham a guarda.
    """
    dados = request.get_json()
    if not isinstance(dados, dict):
        return None
    return dados


def e_numero(valor):
    """Número de verdade, F13. Booleano é `int` em Python e não conta."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def como_numero(texto):
    """Converte argumento de consulta, ou devolve None, F13."""
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None
