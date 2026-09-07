"""Orquestração das requisições de tarefa."""
import logging

from flask import request
from sqlalchemy.exc import SQLAlchemyError

from src.config import settings
from src.controllers import envelope, validators
from src.models import category_model, task_model, user_model

logger = logging.getLogger(__name__)


def _reference_error(user_id, category_id):
    """Ordem idêntica à do handler original: usuário antes de categoria."""
    if user_id and user_model.get_by_id(user_id) is None:
        return "Usuário não encontrado"
    if category_id and category_model.get_by_id(category_id) is None:
        return "Categoria não encontrada"
    return None


def list_tasks():
    tasks = task_model.get_all_with_relations()
    return envelope.ok([task.to_listing_dict() for task in tasks])


def get_task(task_id):
    task = task_model.get_by_id(task_id)
    if task is None:
        return envelope.fail("Task não encontrada", 404)
    return envelope.ok(task.to_dict_with_overdue())


def create_task():
    data = request.get_json()
    if not data:
        return envelope.fail("Dados inválidos", 400)

    error = validators.title_error(data.get("title"))
    if error:
        return envelope.fail(error, 400)

    status = data.get("status", settings.DEFAULT_TASK_STATUS)
    priority = data.get("priority", settings.DEFAULT_PRIORITY)
    user_id = data.get("user_id")
    category_id = data.get("category_id")

    error = validators.status_error(status)
    if error:
        return envelope.fail(error, 400)

    error = validators.priority_error(priority)
    if error:
        return envelope.fail(error, 400)

    error = _reference_error(user_id, category_id)
    if error:
        return envelope.fail(error, 404)

    fields = {
        "title": data.get("title"),
        "description": data.get("description", ""),
        "status": status,
        "priority": priority,
        "user_id": user_id,
        "category_id": category_id,
    }

    raw_due_date = data.get("due_date")
    if raw_due_date:
        due_date = validators.parse_due_date(raw_due_date)
        if due_date is None:
            return envelope.fail("Formato de data inválido. Use YYYY-MM-DD", 400)
        fields["due_date"] = due_date

    tags = data.get("tags")
    if tags:
        fields["tags"] = validators.join_tags(tags)

    try:
        task = task_model.create(fields)
    except SQLAlchemyError:
        logger.exception("falha ao criar task")
        return envelope.fail("Erro ao criar task", 500)

    logger.info("task criada id=%s titulo=%s", task.id, task.title)
    return envelope.ok(task.to_dict(), 201)


def update_task(task_id):
    task = task_model.get_by_id(task_id)
    if task is None:
        return envelope.fail("Task não encontrada", 404)

    data = request.get_json()
    if not data:
        return envelope.fail("Dados inválidos", 400)

    if "title" in data:
        error = validators.title_update_error(data["title"])
        if error:
            return envelope.fail(error, 400)
        task.title = data["title"]

    if "description" in data:
        task.description = data["description"]

    if "status" in data:
        error = validators.status_error(data["status"])
        if error:
            return envelope.fail(error, 400)
        task.status = data["status"]

    if "priority" in data:
        error = validators.priority_error(data["priority"])
        if error:
            return envelope.fail(error, 400)
        task.priority = data["priority"]

    if "user_id" in data:
        if data["user_id"] and user_model.get_by_id(data["user_id"]) is None:
            return envelope.fail("Usuário não encontrado", 404)
        task.user_id = data["user_id"]

    if "category_id" in data:
        if data["category_id"] and category_model.get_by_id(data["category_id"]) is None:
            return envelope.fail("Categoria não encontrada", 404)
        task.category_id = data["category_id"]

    if "due_date" in data:
        if data["due_date"]:
            due_date = validators.parse_due_date(data["due_date"])
            if due_date is None:
                return envelope.fail("Formato de data inválido", 400)
            task.due_date = due_date
        else:
            task.due_date = None

    if "tags" in data:
        task.tags = validators.join_tags(data["tags"])

    try:
        task_model.save(task)
    except SQLAlchemyError:
        logger.exception("falha ao atualizar task id=%s", task_id)
        return envelope.fail("Erro ao atualizar", 500)

    logger.info("task atualizada id=%s", task.id)
    return envelope.ok(task.to_dict())


def delete_task(task_id):
    task = task_model.get_by_id(task_id)
    if task is None:
        return envelope.fail("Task não encontrada", 404)

    try:
        task_model.delete(task)
    except SQLAlchemyError:
        logger.exception("falha ao remover task id=%s", task_id)
        return envelope.fail("Erro ao deletar", 500)

    logger.info("task removida id=%s", task_id)
    return envelope.ok({"message": "Task deletada com sucesso"})


def search_tasks():
    term = request.args.get("q", "")
    status = request.args.get("status", "")
    raw_priority = request.args.get("priority", "")
    raw_user_id = request.args.get("user_id", "")

    priority = None
    if raw_priority:
        priority = validators.as_int(raw_priority)
        if priority is None:
            return envelope.fail("Prioridade inválida", 400)

    user_id = None
    if raw_user_id:
        user_id = validators.as_int(raw_user_id)
        if user_id is None:
            return envelope.fail("Usuário inválido", 400)

    tasks = task_model.search(term, status, priority, user_id)
    return envelope.ok([task.to_dict() for task in tasks])


def task_stats():
    return envelope.ok(task_model.build_stats())
