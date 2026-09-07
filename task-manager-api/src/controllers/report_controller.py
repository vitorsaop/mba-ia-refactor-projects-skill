"""Orquestração das requisições de relatório."""
from src.controllers import envelope
from src.models import report_model, user_model


def summary_report():
    return envelope.ok(report_model.build_summary())


def user_report(user_id):
    user = user_model.get_by_id(user_id)
    if user is None:
        return envelope.fail("Usuário não encontrado", 404)
    return envelope.ok(report_model.build_user_report(user))
