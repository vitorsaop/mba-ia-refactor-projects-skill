from flask import jsonify

from src.models import relatorio_model


def vendas():
    relatorio = relatorio_model.vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200


def health():
    contagens = relatorio_model.contagens_saude()
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": "1.0.0",
        "ambiente": "producao",
        "db_path": "loja.db",
        # C6/CRITICAL da auditoria: debug e secret_key expostos na resposta.
        # Correção (T18) é contract-breaking e não foi autorizada no portão
        # da Fase 2 — preservado de propósito até autorização futura.
        "debug": True,
        "secret_key": "minha-chave-super-secreta-123",
    }), 200
