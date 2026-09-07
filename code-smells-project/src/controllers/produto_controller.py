"""Orquestração das requisições de produto."""
import logging

from flask import request

from src.config.settings import (
    CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX_LENGTH, NOME_PRODUTO_MIN_LENGTH,
)
from src.controllers import envelope, validators
from src.models import produto_model

logger = logging.getLogger(__name__)


def _erro_campos_comuns(dados):
    """Verificações que criar e atualizar já compartilhavam, F12.

    O tamanho de nome e a categoria válida NÃO entram aqui de propósito:
    medido na linha de base, `atualizar` não os verifica, e `PUT /produtos/1`
    com nome de um caractere ou categoria fora da lista devolve 200. Incluí-los
    faria a rota passar a recusar entrada hoje aceita, o que o portão não
    autorizou.
    """
    if not dados:
        return "Dados inválidos"
    if "nome" not in dados:
        return "Nome é obrigatório"
    if "preco" not in dados:
        return "Preço é obrigatório"
    if "estoque" not in dados:
        return "Estoque é obrigatório"
    # F13: comparar sem verificar o tipo levantava TypeError e devolvia 500.
    if not validators.e_numero(dados["preco"]):
        return "Preço inválido"
    if not validators.e_numero(dados["estoque"]):
        return "Estoque inválido"
    if dados["preco"] < 0:
        return "Preço não pode ser negativo"
    if dados["estoque"] < 0:
        return "Estoque não pode ser negativo"
    return None


def listar():
    return envelope.ok(produto_model.get_all())


def buscar(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if produto:
        return envelope.ok(produto)
    return envelope.falha("Produto não encontrado", 404, com_sucesso=True)


def criar():
    dados = validators.corpo_objeto()

    erro = _erro_campos_comuns(dados)
    if erro:
        return envelope.falha(erro, 400)

    nome = dados["nome"]
    categoria = dados.get("categoria", "geral")

    if len(nome) < NOME_PRODUTO_MIN_LENGTH:
        return envelope.falha("Nome muito curto", 400)
    if len(nome) > NOME_PRODUTO_MAX_LENGTH:
        return envelope.falha("Nome muito longo", 400)
    if categoria not in CATEGORIAS_VALIDAS:
        return envelope.falha(
            "Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)), 400)

    produto_id = produto_model.create(
        nome, dados.get("descricao", ""), dados["preco"], dados["estoque"], categoria)
    logger.info("produto criado id=%s", produto_id)
    return envelope.ok({"id": produto_id}, 201, mensagem="Produto criado")


def atualizar(produto_id):
    dados = validators.corpo_objeto()

    if not produto_model.get_by_id(produto_id):
        return envelope.falha("Produto não encontrado", 404)

    erro = _erro_campos_comuns(dados)
    if erro:
        return envelope.falha(erro, 400)

    produto_model.update(
        produto_id, dados["nome"], dados.get("descricao", ""),
        dados["preco"], dados["estoque"], dados.get("categoria", "geral"))
    return envelope.ok({"id": produto_id}, 200, mensagem="Produto atualizado")


def deletar(produto_id):
    if not produto_model.get_by_id(produto_id):
        return envelope.falha("Produto não encontrado", 404)

    produto_model.delete(produto_id)
    logger.info("produto deletado id=%s", produto_id)
    return envelope.ok({"id": produto_id}, 200, mensagem="Produto deletado")


def buscar_varios():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    # F13: `float()` sem bloco protegido levantava ValueError e devolvia 500.
    if preco_min:
        preco_min = validators.como_numero(preco_min)
        if preco_min is None:
            return envelope.falha("Preço mínimo inválido", 400)
    if preco_max:
        preco_max = validators.como_numero(preco_max)
        if preco_max is None:
            return envelope.falha("Preço máximo inválido", 400)

    resultados = produto_model.search(termo, categoria, preco_min, preco_max)
    # A chave `total` faz parte do contrato deste endpoint.
    return envelope.ok(resultados, extras={"total": len(resultados)})
