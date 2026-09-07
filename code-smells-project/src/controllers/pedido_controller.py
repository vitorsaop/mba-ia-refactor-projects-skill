import logging

from src.controllers import envelope, validators
from src.models import pedido_model
from src.config.settings import STATUS_PEDIDO_VALIDOS

logger = logging.getLogger(__name__)


def criar():
    dados = validators.corpo_objeto()
    if not dados:
        return envelope.falha("Dados inválidos", 400)

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return envelope.falha("Usuario ID é obrigatório", 400)
    if not itens or len(itens) == 0:
        return envelope.falha("Pedido deve ter pelo menos 1 item", 400)

    resultado = pedido_model.create(usuario_id, itens)

    if "erro" in resultado:
        return envelope.falha(resultado["erro"], 400, com_sucesso=True)

    logger.info("pedido criado id=%s usuario_id=%s", resultado["pedido_id"], usuario_id)
    logger.info("notificacao simulada (email) para pedido %s", resultado["pedido_id"])
    logger.info("notificacao simulada (sms) para pedido %s", resultado["pedido_id"])
    logger.info("notificacao simulada (push) para pedido %s", resultado["pedido_id"])

    return envelope.ok(resultado, 201, mensagem="Pedido criado com sucesso")


def listar_por_usuario(usuario_id):
    return envelope.ok(pedido_model.get_by_usuario(usuario_id))


def listar_todos():
    return envelope.ok(pedido_model.get_all())


def atualizar_status(pedido_id):
    dados = validators.corpo_objeto()
    if dados is None:
        return envelope.falha("Dados inválidos", 400)

    novo_status = dados.get("status", "")

    if novo_status not in STATUS_PEDIDO_VALIDOS:
        return envelope.falha("Status inválido", 400)

    # F11: a escrita ocorria sem verificar a existência, e um identificador
    # inexistente devolvia 200 com mensagem de sucesso.
    if not pedido_model.get_by_id(pedido_id):
        return envelope.falha("Pedido não encontrado", 404)

    pedido_model.update_status(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("pedido %s aprovado, preparar envio", pedido_id)
    if novo_status == "cancelado":
        logger.info("pedido %s cancelado, devolver estoque", pedido_id)

    return envelope.ok_sem_dados(200, mensagem="Status atualizado")
