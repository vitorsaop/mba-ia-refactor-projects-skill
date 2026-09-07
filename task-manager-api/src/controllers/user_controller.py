"""Orquestração das requisições de usuário."""
import logging

from flask import request
from sqlalchemy.exc import SQLAlchemyError

from src.config import settings
from src.controllers import envelope, validators
from src.models import task_model, user_model

logger = logging.getLogger(__name__)


def list_users():
    return envelope.ok(user_model.list_with_task_count())


def get_user(user_id):
    user = user_model.get_by_id(user_id)
    if user is None:
        return envelope.fail("Usuário não encontrado", 404)

    data = user.to_dict()
    data["tasks"] = [task.to_dict() for task in task_model.get_by_user(user_id)]
    return envelope.ok(data)


def create_user():
    data = request.get_json()
    if not data:
        return envelope.fail("Dados inválidos", 400)

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", settings.DEFAULT_USER_ROLE)

    # Ordem idêntica à do handler original.
    if not name:
        return envelope.fail("Nome é obrigatório", 400)
    if not email:
        return envelope.fail("Email é obrigatório", 400)
    if not password:
        return envelope.fail("Senha é obrigatória", 400)

    if not validators.is_valid_email(email):
        return envelope.fail("Email inválido", 400)

    # Sem guarda de tipo: ver a nota em validators.is_valid_email.
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        return envelope.fail("Senha deve ter no mínimo 4 caracteres", 400)

    if user_model.get_by_email(email) is not None:
        return envelope.fail("Email já cadastrado", 409)

    error = validators.role_error(role)
    if error:
        return envelope.fail(error, 400)

    try:
        user = user_model.create(name, email, password, role)
    except SQLAlchemyError:
        logger.exception("falha ao criar usuario")
        return envelope.fail("Erro ao criar usuário", 500)

    logger.info("usuario criado id=%s nome=%s", user.id, user.name)
    return envelope.ok(user.to_dict(), 201)


def update_user(user_id):
    user = user_model.get_by_id(user_id)
    if user is None:
        return envelope.fail("Usuário não encontrado", 404)

    data = request.get_json()
    if not data:
        return envelope.fail("Dados inválidos", 400)

    if "name" in data:
        # F38: a rota de criação exige nome; a de atualização aceitava
        # qualquer valor. Autorizado no item [7] do portão.
        if not validators.is_filled_text(data["name"]):
            return envelope.fail("Nome é obrigatório", 400)
        user.name = data["name"]

    if "email" in data:
        if not validators.is_valid_email(data["email"]):
            return envelope.fail("Email inválido", 400)
        if user_model.email_taken_by_other(data["email"], user_id):
            return envelope.fail("Email já cadastrado", 409)
        user.email = data["email"]

    if "password" in data:
        if len(data["password"]) < settings.MIN_PASSWORD_LENGTH:
            return envelope.fail("Senha muito curta", 400)
        user.set_password(data["password"])

    if "role" in data:
        error = validators.role_error(data["role"])
        if error:
            return envelope.fail(error, 400)
        user.role = data["role"]

    if "active" in data:
        user.active = data["active"]

    try:
        user_model.save()
    except SQLAlchemyError:
        logger.exception("falha ao atualizar usuario id=%s", user_id)
        return envelope.fail("Erro ao atualizar", 500)

    return envelope.ok(user.to_dict())


def delete_user(user_id):
    user = user_model.get_by_id(user_id)
    if user is None:
        return envelope.fail("Usuário não encontrado", 404)

    try:
        user_model.delete_with_tasks(user)
    except SQLAlchemyError:
        logger.exception("falha ao remover usuario id=%s", user_id)
        return envelope.fail("Erro ao deletar", 500)

    logger.info("usuario removido id=%s", user_id)
    return envelope.ok({"message": "Usuário deletado com sucesso"})


def get_user_tasks(user_id):
    user = user_model.get_by_id(user_id)
    if user is None:
        return envelope.fail("Usuário não encontrado", 404)

    tasks = task_model.get_by_user(user_id)
    return envelope.ok([task.to_user_listing_dict() for task in tasks])


def login():
    data = request.get_json()
    if not data:
        return envelope.fail("Dados inválidos", 400)

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return envelope.fail("Email e senha são obrigatórios", 400)

    user = user_model.get_by_email(email)
    if user is None:
        return envelope.fail("Credenciais inválidas", 401)

    if not user.check_password(password):
        return envelope.fail("Credenciais inválidas", 401)

    if not user.active:
        return envelope.fail("Usuário inativo", 403)

    return envelope.ok({
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": settings.TOKEN_PREFIX + str(user.id),
    })
