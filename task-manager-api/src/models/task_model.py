"""Modelo de tarefa: dados, invariantes e regra de atraso."""
from src.config import settings
from src.config.clock import utcnow
from src.config.database import db


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=settings.DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=settings.DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    def to_dict(self):
        """As 11 chaves da serialização original, na mesma ordem de leitura.

        A chave `overdue` NÃO entra aqui. Medido na linha de base: ela está
        presente em `GET /tasks`, `GET /tasks/<id>` e `GET /users/<id>/tasks`,
        e ausente em `GET /tasks/search`, `POST /tasks` e `PUT /tasks/<id>`,
        que consomem esta serialização. Acrescentá-la aqui mudaria o corpo de
        três endpoints, o que a regra permanente 4 proíbe.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "tags": self.tags.split(settings.TAG_SEPARATOR) if self.tags else [],
        }

    def to_dict_with_overdue(self):
        """Consumida por `GET /tasks/<id>`."""
        data = self.to_dict()
        data["overdue"] = self.is_overdue()
        return data

    def to_listing_dict(self):
        """Consumida por `GET /tasks`: acrescenta atraso e os nomes resolvidos."""
        data = self.to_dict_with_overdue()
        data["user_name"] = self.user.name if self.user else None
        data["category_name"] = self.category.name if self.category else None
        return data

    def to_user_listing_dict(self):
        """Consumida por `GET /users/<id>/tasks`: subconjunto de 8 chaves."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": str(self.created_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "overdue": self.is_overdue(),
        }

    def is_overdue(self):
        """Regra de atraso, ponto único. Antes duplicada em cinco handlers."""
        if not self.due_date:
            return False
        if self.due_date >= utcnow():
            return False
        return self.status not in settings.TERMINAL_TASK_STATUSES

    def days_overdue(self):
        return (utcnow() - self.due_date).days

    def is_high_priority(self):
        return self.priority <= settings.HIGH_PRIORITY_MAX


def _with_relations(statement):
    """Carga antecipada, T7. Remove as duas consultas por tarefa de `GET /tasks`."""
    return statement.options(
        db.joinedload(Task.user), db.joinedload(Task.category)
    )


def _commit():
    """Confirma, e desfaz no erro. A transacao abre e fecha na mesma camada."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def get_by_id(task_id):
    return db.session.get(Task, task_id)


def get_all():
    return db.session.execute(db.select(Task)).scalars().all()


def get_all_with_relations():
    return db.session.execute(
        _with_relations(db.select(Task))
    ).unique().scalars().all()


def get_by_user(user_id):
    return db.session.execute(
        db.select(Task).where(Task.user_id == user_id)
    ).scalars().all()


def count():
    return db.session.execute(
        db.select(db.func.count()).select_from(Task)
    ).scalar()


def count_by_status(status):
    return db.session.execute(
        db.select(db.func.count()).select_from(Task).where(Task.status == status)
    ).scalar()


def count_by_priority(priority):
    return db.session.execute(
        db.select(db.func.count()).select_from(Task).where(Task.priority == priority)
    ).scalar()


def count_created_since(moment):
    return db.session.execute(
        db.select(db.func.count()).select_from(Task).where(Task.created_at >= moment)
    ).scalar()


def count_done_since(moment):
    return db.session.execute(
        db.select(db.func.count()).select_from(Task)
        .where(Task.status == "done", Task.updated_at >= moment)
    ).scalar()


def search(term, status, priority, user_id):
    """Filtros combináveis. Todo valor entra como parâmetro, nunca no texto."""
    statement = db.select(Task)
    if term:
        pattern = f"%{term}%"
        statement = statement.where(
            db.or_(Task.title.like(pattern), Task.description.like(pattern))
        )
    if status:
        statement = statement.where(Task.status == status)
    if priority is not None:
        statement = statement.where(Task.priority == priority)
    if user_id is not None:
        statement = statement.where(Task.user_id == user_id)
    return db.session.execute(statement).scalars().all()


def count_overdue():
    return sum(1 for task in get_all() if task.is_overdue())


def build_stats():
    """Corpo de `GET /tasks/stats`. Mesmas chaves, mesmos valores."""
    from src.models.report_model import percentage

    total = count()
    counts = {status: count_by_status(status)
              for status in settings.VALID_TASK_STATUSES}
    stats = dict(counts)
    stats["total"] = total
    stats["overdue"] = count_overdue()
    stats["completion_rate"] = percentage(counts["done"], total)
    return stats


def create(fields):
    task = Task()
    task.title = fields["title"]
    task.description = fields["description"]
    task.status = fields["status"]
    task.priority = fields["priority"]
    task.user_id = fields["user_id"]
    task.category_id = fields["category_id"]
    task.due_date = fields.get("due_date")
    task.tags = fields.get("tags")
    db.session.add(task)
    _commit()
    return task


def save(task):
    task.updated_at = utcnow()
    _commit()
    return task


def delete(task):
    db.session.delete(task)
    _commit()
