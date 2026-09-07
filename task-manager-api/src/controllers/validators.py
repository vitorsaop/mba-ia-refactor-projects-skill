"""Validação de formato de entrada.

Reúne as verificações que estavam por extenso nos handlers e as funções que o
módulo de apoio já definia e ninguém chamava.
"""
import re
from datetime import datetime

from src.config import settings

_EMAIL = re.compile(settings.EMAIL_PATTERN)


def is_valid_email(email):
    """Sem guarda de tipo, de proposito.

    O handler original chamava `re.match` direto sobre o valor recebido, e um
    valor não textual levantava `TypeError`. O portão autorizou 400 para tipo
    inválido apenas em tasks, F36. Acrescentar a guarda aqui mudaria o
    contrato de `POST /users` e `PUT /users/<id>`, que ninguém autorizou.
    """
    return bool(_EMAIL.match(email))


def is_valid_color(color):
    return (isinstance(color, str)
            and len(color) == settings.COLOR_LENGTH
            and color[0] == settings.COLOR_PREFIX)


def is_text(value):
    """Guarda de tipo usada apenas onde o portão autorizou 400 para tipo
    inválido: título de task, F36, e a data limite, cujo `strptime` já
    levantava e caía no 400 original."""
    return isinstance(value, str)


def is_filled_text(value):
    return isinstance(value, str) and bool(value)


def is_int(value):
    """Inteiro de verdade. Booleano é `int` em Python e não conta."""
    return isinstance(value, int) and not isinstance(value, bool)


def as_int(value):
    """Converte argumento de consulta para inteiro, ou devolve None.

    Usada apenas no caminho de `GET /tasks/search`, onde o handler original já
    chamava `int()` sobre o texto da consulta.
    """
    if is_int(value):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def title_error(title):
    """Ordem idêntica à do handler original: obrigatório, curto, longo."""
    if not title:
        return "Título é obrigatório"
    if not is_text(title):
        return "Título inválido"
    if len(title) < settings.MIN_TITLE_LENGTH:
        return "Título muito curto"
    if len(title) > settings.MAX_TITLE_LENGTH:
        return "Título muito longo"
    return None


def title_update_error(title):
    """Na atualização o campo não é obrigatório, apenas medido."""
    if not is_text(title):
        return "Título inválido"
    if len(title) < settings.MIN_TITLE_LENGTH:
        return "Título muito curto"
    if len(title) > settings.MAX_TITLE_LENGTH:
        return "Título muito longo"
    return None


def status_error(status):
    if status not in settings.VALID_TASK_STATUSES:
        return "Status inválido"
    return None


def priority_error(priority):
    """Recusa tipo não inteiro, F36.

    A linha de base comparava direto e levantava `TypeError`, devolvendo 500.
    O portão autorizou 400 para tipo inválido, não a aceitação de texto
    numérico: `is_int` recusa `"3"` do mesmo jeito que recusa `"alta"`.
    """
    if not is_int(priority):
        return "Prioridade inválida"
    if priority < settings.MIN_PRIORITY or priority > settings.MAX_PRIORITY:
        return "Prioridade deve ser entre 1 e 5"
    return None


def role_error(role):
    if role not in settings.VALID_USER_ROLES:
        return "Role inválido"
    return None


def parse_due_date(value):
    """Aceita apenas o formato documentado. Devolve None quando não casa."""
    if not is_text(value):
        return None
    try:
        return datetime.strptime(value, settings.DUE_DATE_FORMAT)
    except ValueError:
        return None


def join_tags(tags):
    if isinstance(tags, list):
        return settings.TAG_SEPARATOR.join(tags)
    return tags
