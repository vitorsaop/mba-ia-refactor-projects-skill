"""Camada de rotas: associação entre caminho, método e controller.

Nenhum handler é definido aqui. As 22 associações reproduzem o inventário da
Fase 1 com o mesmo caminho e o mesmo método.
"""
from flask import Blueprint

from src.controllers import (
    category_controller,
    health_controller,
    report_controller,
    task_controller,
    user_controller,
)
from src.middlewares.admin_guard import require_admin

root_bp = Blueprint("root", __name__)
task_bp = Blueprint("tasks", __name__)
user_bp = Blueprint("users", __name__)
report_bp = Blueprint("reports", __name__)

root_bp.add_url_rule("/", "index", health_controller.index, methods=["GET"])
root_bp.add_url_rule("/health", "health", health_controller.health, methods=["GET"])

task_bp.add_url_rule("/tasks", "get_tasks",
                     task_controller.list_tasks, methods=["GET"])
task_bp.add_url_rule("/tasks", "create_task",
                     task_controller.create_task, methods=["POST"])
task_bp.add_url_rule("/tasks/search", "search_tasks",
                     task_controller.search_tasks, methods=["GET"])
task_bp.add_url_rule("/tasks/stats", "task_stats",
                     task_controller.task_stats, methods=["GET"])
task_bp.add_url_rule("/tasks/<int:task_id>", "get_task",
                     task_controller.get_task, methods=["GET"])
task_bp.add_url_rule("/tasks/<int:task_id>", "update_task",
                     task_controller.update_task, methods=["PUT"])
task_bp.add_url_rule("/tasks/<int:task_id>", "delete_task",
                     require_admin(task_controller.delete_task), methods=["DELETE"])

user_bp.add_url_rule("/users", "get_users",
                     user_controller.list_users, methods=["GET"])
user_bp.add_url_rule("/users", "create_user",
                     user_controller.create_user, methods=["POST"])
user_bp.add_url_rule("/users/<int:user_id>", "get_user",
                     user_controller.get_user, methods=["GET"])
user_bp.add_url_rule("/users/<int:user_id>", "update_user",
                     user_controller.update_user, methods=["PUT"])
user_bp.add_url_rule("/users/<int:user_id>", "delete_user",
                     require_admin(user_controller.delete_user), methods=["DELETE"])
user_bp.add_url_rule("/users/<int:user_id>/tasks", "get_user_tasks",
                     user_controller.get_user_tasks, methods=["GET"])
user_bp.add_url_rule("/login", "login",
                     user_controller.login, methods=["POST"])

report_bp.add_url_rule("/reports/summary", "summary_report",
                       report_controller.summary_report, methods=["GET"])
report_bp.add_url_rule("/reports/user/<int:user_id>", "user_report",
                       report_controller.user_report, methods=["GET"])
report_bp.add_url_rule("/categories", "get_categories",
                       category_controller.list_categories, methods=["GET"])
report_bp.add_url_rule("/categories", "create_category",
                       category_controller.create_category, methods=["POST"])
report_bp.add_url_rule("/categories/<int:category_id>", "update_category",
                       category_controller.update_category, methods=["PUT"])
report_bp.add_url_rule("/categories/<int:category_id>", "delete_category",
                       require_admin(category_controller.delete_category),
                       methods=["DELETE"])

BLUEPRINTS = (root_bp, task_bp, user_bp, report_bp)
