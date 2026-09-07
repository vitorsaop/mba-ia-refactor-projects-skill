"""Orquestração das requisições de categoria."""
import logging

from flask import request
from sqlalchemy.exc import SQLAlchemyError

from src.config import settings
from src.controllers import envelope, validators
from src.models import category_model

logger = logging.getLogger(__name__)


def list_categories():
    return envelope.ok(category_model.list_with_task_count())


def create_category():
    data = request.get_json()
    if not data:
        return envelope.fail("Dados inválidos", 400)

    name = data.get("name")
    if not name:
        return envelope.fail("Nome é obrigatório", 400)

    color = data.get("color", settings.DEFAULT_COLOR)
    # F31, item [5] do portão: a cor era aceita sem verificação de formato,
    # embora o projeto já definisse a verificação e não a chamasse.
    if not validators.is_valid_color(color):
        return envelope.fail("Cor inválida", 400)

    try:
        category = category_model.create(name, data.get("description", ""), color)
    except SQLAlchemyError:
        logger.exception("falha ao criar categoria")
        return envelope.fail("Erro ao criar categoria", 500)

    return envelope.ok(category.to_dict(), 201)


def update_category(category_id):
    category = category_model.get_by_id(category_id)
    if category is None:
        return envelope.fail("Categoria não encontrada", 404)

    data = request.get_json()

    if "name" in data:
        # F31: a rota de atualização não validava nada e aceitava nome vazio,
        # estado que a rota de criação recusa.
        if not validators.is_filled_text(data["name"]):
            return envelope.fail("Nome é obrigatório", 400)
        category.name = data["name"]

    if "description" in data:
        category.description = data["description"]

    if "color" in data:
        if not validators.is_valid_color(data["color"]):
            return envelope.fail("Cor inválida", 400)
        category.color = data["color"]

    try:
        category_model.save()
    except SQLAlchemyError:
        logger.exception("falha ao atualizar categoria id=%s", category_id)
        return envelope.fail("Erro ao atualizar", 500)

    return envelope.ok(category.to_dict())


def delete_category(category_id):
    category = category_model.get_by_id(category_id)
    if category is None:
        return envelope.fail("Categoria não encontrada", 404)

    try:
        category_model.delete(category)
    except SQLAlchemyError:
        logger.exception("falha ao remover categoria id=%s", category_id)
        return envelope.fail("Erro ao deletar", 500)

    return envelope.ok({"message": "Categoria deletada"})
