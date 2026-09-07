"""Modelo de usuário: dados, invariantes e derivação de senha."""
import hashlib
import hmac
import os

from src.config import settings
from src.config.clock import utcnow
from src.config.database import db


def hash_password(raw_password):
    """Deriva a senha com sal por usuário, T17. Biblioteca padrão."""
    salt = os.urandom(settings.PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        settings.PASSWORD_ALGORITHM, raw_password.encode(), salt,
        settings.PASSWORD_ITERATIONS,
    )
    return (f"pbkdf2_{settings.PASSWORD_ALGORITHM}${settings.PASSWORD_ITERATIONS}"
            f"${salt.hex()}${digest.hex()}")


def verify_password(raw_password, stored):
    """Compara em tempo constante. Digest em formato antigo não valida."""
    if not stored:
        return False
    try:
        prefix, iterations, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if not prefix.startswith("pbkdf2_"):
        return False
    algorithm = prefix[len("pbkdf2_"):]
    try:
        digest = hashlib.pbkdf2_hmac(
            algorithm, raw_password.encode(), bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=settings.DEFAULT_USER_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Serialização pública. A chave `password` foi removida por F03, T18."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def to_summary_dict(self, task_count=None):
        """Consumida pela listagem, que expõe a contagem de tarefas.

        A contagem vem por parâmetro para que a listagem faça uma consulta
        agrupada em vez de uma por usuário.
        """
        data = self.to_dict()
        data["task_count"] = len(self.tasks) if task_count is None else task_count
        return data

    def to_identity_dict(self):
        """Consumida pelo relatório por usuário: só identificação."""
        return {"id": self.id, "name": self.name, "email": self.email}

    def set_password(self, raw_password):
        self.password = hash_password(raw_password)

    def check_password(self, raw_password):
        return verify_password(raw_password, self.password)


def _commit():
    """Confirma, e desfaz no erro. A transacao abre e fecha na mesma camada."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def get_by_id(user_id):
    return db.session.get(User, user_id)


def get_all():
    return db.session.execute(db.select(User)).scalars().all()


def task_counts_by_user():
    """Contagem agrupada, T7.

    Usuário sem tarefa não aparece, e quem consome usa 0 como valor de
    reserva, que é o mesmo resultado de `len(user.tasks)`.
    """
    from src.models.task_model import Task

    rows = db.session.execute(
        db.select(Task.user_id, db.func.count(Task.id)).group_by(Task.user_id)
    ).all()
    return {user_id: total for user_id, total in rows}


def list_with_task_count():
    """Corpo de `GET /users`: usuário mais contagem de tarefas."""
    counts = task_counts_by_user()
    return [user.to_summary_dict(counts.get(user.id, 0)) for user in get_all()]


def get_by_email(email):
    return db.session.execute(
        db.select(User).where(User.email == email)
    ).scalars().first()


def count():
    return db.session.execute(
        db.select(db.func.count()).select_from(User)
    ).scalar()


def email_taken_by_other(email, user_id):
    existing = get_by_email(email)
    return existing is not None and existing.id != user_id


def create(name, email, raw_password, role):
    user = User()
    user.name = name
    user.email = email
    user.set_password(raw_password)
    user.role = role
    db.session.add(user)
    _commit()
    return user


def save():
    _commit()


def delete_with_tasks(user):
    """Remoção em cascata das tarefas do usuário, F18.

    A regra vivia no handler de rota. Passa a ser operação de domínio, dentro
    da mesma sessão transacional, portanto o resultado no banco é idêntico.
    """
    from src.models import task_model

    for task in task_model.get_by_user(user.id):
        db.session.delete(task)
    db.session.delete(user)
    _commit()
