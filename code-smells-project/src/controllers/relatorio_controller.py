from src.config import settings
from src.controllers import envelope
from src.models import relatorio_model


def vendas():
    return envelope.ok(relatorio_model.vendas())


def health():
    # F04: as chaves `debug` e `secret_key` saíram do corpo. F05: com elas saiu
    # a última ocorrência do literal da chave secreta no código.
    # F15: versão, ambiente e caminho do banco vêm da configuração.
    return envelope.ok({
        "status": "ok",
        "database": "connected",
        "counts": relatorio_model.contagens_saude(),
        "versao": settings.VERSAO,
        "ambiente": settings.AMBIENTE,
        "db_path": settings.DB_PATH,
    })
