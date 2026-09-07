"""Agregações de relatório. A regra saiu dos handlers de rota, F13."""
from datetime import timedelta

from src.config import settings
from src.config.clock import utcnow
from src.models import category_model, task_model, user_model


def percentage(part, total):
    """Ponto único da taxa de conclusão, antes duplicada em três handlers.

    Devolve inteiro 0 quando o total é zero e float arredondado a duas casas
    caso contrário, exatamente como as três expressões originais.
    """
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def _counts_by_status(tasks):
    counts = {status: 0 for status in settings.VALID_TASK_STATUSES}
    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
    return counts


def _group_by_user(tasks):
    """Agrupa em memória as tarefas já carregadas, T7.

    Substitui a consulta por usuário do laço original e reusa a lista que
    `build_summary` já carregou, em vez de ler a tabela uma segunda vez.
    """
    grouped = {}
    for task in tasks:
        grouped.setdefault(task.user_id, []).append(task)
    return grouped


def build_summary():
    """Corpo de `GET /reports/summary`. Mesmas chaves, mesmos valores."""
    all_tasks = task_model.get_all()

    overdue_list = []
    for task in all_tasks:
        if task.is_overdue():
            overdue_list.append({
                "id": task.id,
                "title": task.title,
                "due_date": str(task.due_date),
                "days_overdue": task.days_overdue(),
            })

    moment = utcnow() - timedelta(days=settings.RECENT_ACTIVITY_DAYS)
    grouped = _group_by_user(all_tasks)

    user_stats = []
    for user in user_model.get_all():
        tasks = grouped.get(user.id, [])
        total = len(tasks)
        completed = sum(1 for task in tasks if task.status == "done")
        user_stats.append({
            "user_id": user.id,
            "user_name": user.name,
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": percentage(completed, total),
        })

    return {
        "generated_at": str(utcnow()),
        "overview": {
            "total_tasks": task_model.count(),
            "total_users": user_model.count(),
            "total_categories": category_model.count(),
        },
        "tasks_by_status": {
            status: task_model.count_by_status(status)
            for status in settings.VALID_TASK_STATUSES
        },
        "tasks_by_priority": {
            label: task_model.count_by_priority(priority)
            for priority, label in settings.PRIORITY_LABELS
        },
        "overdue": {
            "count": len(overdue_list),
            "tasks": overdue_list,
        },
        "recent_activity": {
            "tasks_created_last_7_days": task_model.count_created_since(moment),
            "tasks_completed_last_7_days": task_model.count_done_since(moment),
        },
        "user_productivity": user_stats,
    }


def build_user_report(user):
    """Corpo de `GET /reports/user/<id>`. Mesmas chaves, mesmos valores."""
    tasks = task_model.get_by_user(user.id)
    counts = _counts_by_status(tasks)
    total = len(tasks)

    return {
        "user": user.to_identity_dict(),
        "statistics": {
            "total_tasks": total,
            "done": counts["done"],
            "pending": counts["pending"],
            "in_progress": counts["in_progress"],
            "cancelled": counts["cancelled"],
            "overdue": sum(1 for task in tasks if task.is_overdue()),
            "high_priority": sum(1 for task in tasks if task.is_high_priority()),
            "completion_rate": percentage(counts["done"], total),
        },
    }
