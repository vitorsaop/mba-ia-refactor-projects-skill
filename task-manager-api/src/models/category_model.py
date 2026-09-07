"""Modelo de categoria."""
from src.config import settings
from src.config.clock import utcnow
from src.config.database import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=settings.DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
        }


def _commit():
    """Confirma, e desfaz no erro. A transacao abre e fecha na mesma camada."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def get_by_id(category_id):
    return db.session.get(Category, category_id)


def get_all():
    return db.session.execute(db.select(Category)).scalars().all()


def count():
    return db.session.execute(
        db.select(db.func.count()).select_from(Category)
    ).scalar()


def create(name, description, color):
    category = Category()
    category.name = name
    category.description = description
    category.color = color
    db.session.add(category)
    _commit()
    return category


def save():
    _commit()


def delete(category):
    db.session.delete(category)
    _commit()


def list_with_task_count():
    """Corpo de `GET /categories`: categoria mais contagem de tarefas."""
    counts = task_counts_by_category()
    result = []
    for category in get_all():
        data = category.to_dict()
        data["task_count"] = counts.get(category.id, 0)
        result.append(data)
    return result


def task_counts_by_category():
    """Contagem agrupada, T7. Substitui uma consulta por categoria.

    Devolve dicionário de `category_id` para contagem. Categoria sem tarefa
    não aparece, e quem consome usa 0 como valor de reserva, que é o mesmo
    resultado que a contagem individual produzia.
    """
    from src.models.task_model import Task

    rows = db.session.execute(
        db.select(Task.category_id, db.func.count(Task.id)).group_by(Task.category_id)
    ).all()
    return {category_id: total for category_id, total in rows}
