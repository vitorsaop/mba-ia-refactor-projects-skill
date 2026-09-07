import logging

from src.controllers import envelope, validators
from src.models import usuario_model

logger = logging.getLogger(__name__)


def listar():
    return envelope.ok(usuario_model.get_all())


def buscar(usuario_id):
    usuario = usuario_model.get_by_id(usuario_id)
    if usuario:
        return envelope.ok(usuario)
    return envelope.falha("Usuário não encontrado", 404)


def criar():
    dados = validators.corpo_objeto()
    if not dados:
        return envelope.falha("Dados inválidos", 400)

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return envelope.falha("Nome, email e senha são obrigatórios", 400)

    usuario_id = usuario_model.create(nome, email, senha)
    logger.info("usuario criado email=%s", email)
    return envelope.ok({"id": usuario_id}, 201)


def login():
    dados = validators.corpo_objeto()
    if dados is None:
        return envelope.falha("Dados inválidos", 400)

    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return envelope.falha("Email e senha são obrigatórios", 400)

    usuario = usuario_model.login(email, senha)
    if usuario:
        logger.info("login bem-sucedido email=%s", email)
        return envelope.ok(usuario, 200, mensagem="Login OK")

    logger.info("login falhou email=%s", email)
    return envelope.falha("Email ou senha inválidos", 401, com_sucesso=True)
