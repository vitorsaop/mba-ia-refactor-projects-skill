#!/usr/bin/env python3
"""Compara duas capturas de comportamento e reporta divergências.

Uso:
    compare.py baseline.json after.json [--expected ARQUIVO] [chave_volátil ...]

Sem `--expected`, qualquer divergência entre as duas capturas reprova.

Com `--expected`, o arquivo declara as divergências que uma correção autorizada
no portão da Fase 2 deve produzir. O arquivo é usado nos dois sentidos:

    declarada e observada       -> autorizada, não reprova
    não declarada               -> reprova
    declarada e não observada   -> reprova

O terceiro caso é o que detecta a correção autorizada que não foi aplicada.

Saída 0: nenhuma divergência não autorizada, e toda divergência declarada foi
         observada.
Saída 1: ao menos uma divergência não autorizada, ou uma divergência declarada
         que não ocorreu.
Saída 2: uso incorreto, captura ausente, vazia ou com JSON inválido.
"""
import json
import re
import sys

# Chaves cujo valor é gerado no momento da requisição e por isso difere entre
# duas execuções. Para essas chaves compara-se apenas presença e tipo.
VOLATEIS = {
    "criado_em", "atualizado_em", "created_at", "updated_at",
    "timestamp", "generated_at",
}


def divergencia(request, chave, tipo, detalhe):
    return {"request": request, "key": chave, "kind": tipo, "detail": detalhe}


def comparar(esperado, obtido, chave, request, erros):
    if isinstance(esperado, dict) and isinstance(obtido, dict):
        for nome in sorted(set(esperado) | set(obtido)):
            local = f"{chave}.{nome}"
            if nome not in esperado:
                erros.append(divergencia(request, local, "acrescentada",
                                         "chave acrescentada"))
            elif nome not in obtido:
                erros.append(divergencia(request, local, "removida",
                                         "chave removida"))
            elif nome in VOLATEIS:
                tipo_esperado = type(esperado[nome]).__name__
                tipo_obtido = type(obtido[nome]).__name__
                if tipo_esperado != tipo_obtido:
                    erros.append(divergencia(
                        request, local, "tipo",
                        f"tipo {tipo_esperado} -> {tipo_obtido}"))
            else:
                comparar(esperado[nome], obtido[nome], local, request, erros)
    elif isinstance(esperado, list) and isinstance(obtido, list):
        if len(esperado) != len(obtido):
            erros.append(divergencia(
                request, chave, "tamanho",
                f"tamanho da lista {len(esperado)} -> {len(obtido)}"))
            return
        for indice, (a, b) in enumerate(zip(esperado, obtido)):
            comparar(a, b, f"{chave}[{indice}]", request, erros)
    elif type(esperado).__name__ != type(obtido).__name__:
        erros.append(divergencia(
            request, chave, "tipo",
            f"tipo {type(esperado).__name__} -> {type(obtido).__name__}"))
    elif esperado != obtido:
        erros.append(divergencia(request, chave, "valor",
                                 f"{esperado!r} -> {obtido!r}"))


def carregar(caminho):
    """Lê uma captura, devolvendo (registros, erro)."""
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except FileNotFoundError:
        return None, f"captura não encontrada: {caminho}"
    except json.JSONDecodeError as exc:
        return None, (
            f"captura inválida em {caminho}: {exc}. "
            "Isso ocorre quando o laço de captura foi interrompido no meio. "
            "Refazer a captura."
        )
    if not isinstance(dados, list):
        return None, f"captura inválida em {caminho}: esperado uma lista"
    if not dados:
        return None, f"captura vazia em {caminho}: nenhuma requisição registrada"
    return dados, None


def carregar_regras(caminho):
    """Lê o arquivo de mudanças esperadas, devolvendo (regras, erro)."""
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except FileNotFoundError:
        return None, f"arquivo de mudanças esperadas não encontrado: {caminho}"
    except json.JSONDecodeError as exc:
        return None, f"arquivo de mudanças esperadas inválido: {exc}"
    if isinstance(dados, dict):
        dados = dados.get("expected", [])
    if not isinstance(dados, list):
        return None, "arquivo de mudanças esperadas: esperado uma lista"
    regras = []
    for indice, bruto in enumerate(dados):
        if not isinstance(bruto, dict):
            return None, f"regra {indice}: esperado um objeto"
        # Correção autorizada cuja mudança não aparece na captura. A verificação
        # que a substitui é cobrada pelo registro de remediação, não aqui.
        if bruto.get("observable") is False:
            continue
        faltando = [c for c in ("finding", "request", "key") if c not in bruto]
        if faltando:
            return None, (
                f"regra {indice}: campo obrigatório ausente: "
                f"{', '.join(faltando)}"
            )
        regras.append({
            "finding": bruto["finding"],
            "request": bruto["request"],
            "key": bruto["key"],
            "kind": bruto.get("kind"),
            "usos": 0,
        })
    return regras, None


_CACHE = {}


def _padrao(texto):
    """Compila um padrão em que `*` é o único curinga.

    `fnmatch` não serve aqui: ele trata `[` e `]` como classe de caractere, e as
    chaves geradas para itens de lista contêm colchetes. O padrão
    `body.dados[*].senha` nunca casaria com `body.dados[0].senha`.
    """
    if texto not in _CACHE:
        _CACHE[texto] = re.compile(
            "^" + ".*".join(re.escape(parte) for parte in texto.split("*")) + "$"
        )
    return _CACHE[texto]


def casa(regra, item):
    if not _padrao(regra["request"]).match(item["request"]):
        return False
    if not _padrao(regra["key"]).match(item["key"]):
        return False
    if regra["kind"] and regra["kind"] != item["kind"]:
        return False
    return True


def main():
    argumentos = sys.argv[1:]
    esperadas = None
    posicionais = []
    indice = 0
    while indice < len(argumentos):
        atual = argumentos[indice]
        if atual == "--expected":
            if indice + 1 >= len(argumentos):
                print("uso: --expected exige o caminho de um arquivo")
                return 2
            esperadas = argumentos[indice + 1]
            indice += 2
            continue
        posicionais.append(atual)
        indice += 1

    if len(posicionais) < 2:
        print("uso: compare.py baseline.json after.json "
              "[--expected ARQUIVO] [chave_volatil ...]")
        return 2

    VOLATEIS.update(posicionais[2:])

    regras = []
    if esperadas is not None:
        regras, erro = carregar_regras(esperadas)
        if erro:
            print(f"ERRO: {erro}")
            return 2

    base, erro = carregar(posicionais[0])
    if erro:
        print(f"ERRO: {erro}")
        return 2
    novo, erro = carregar(posicionais[1])
    if erro:
        print(f"ERRO: {erro}")
        return 2

    erros = []

    if len(base) != len(novo):
        erros.append(divergencia(
            "-", "-", "contagem",
            f"número de requisições {len(base)} -> {len(novo)}"))

    for indice, (a, b) in enumerate(zip(base, novo)):
        rotulo = f"{a['method']} {a['path']}"
        if (a["method"], a["path"]) != (b["method"], b["path"]):
            erros.append(divergencia(
                rotulo, "-", "ordem",
                f"[{indice}] requisição fora de ordem: {rotulo} -> "
                f"{b['method']} {b['path']}"))
            continue
        if a["status"] != b["status"]:
            erros.append(divergencia(
                rotulo, "status", "status",
                f"status {a['status']} -> {b['status']}"))
        comparar(a["body"], b["body"], "body", rotulo, erros)

    autorizadas = []
    nao_autorizadas = []
    for item in erros:
        casadas = [r for r in regras if casa(r, item)]
        if casadas:
            for regra in casadas:
                regra["usos"] += 1
            item["finding"] = casadas[0]["finding"]
            autorizadas.append(item)
        else:
            nao_autorizadas.append(item)

    ausentes = [r for r in regras if r["usos"] == 0]

    if autorizadas:
        print(f"Divergências autorizadas ({len(autorizadas)}):")
        for item in autorizadas:
            print(f"  {item['finding']}: {item['request']} {item['key']}: "
                  f"{item['detail']}")

    if nao_autorizadas or ausentes:
        total = len(nao_autorizadas) + len(ausentes)
        print(f"REPROVADO: {total} divergência(s)")
        for item in nao_autorizadas:
            print(f"  não autorizada: {item['request']} {item['key']}: "
                  f"{item['detail']}")
        for regra in ausentes:
            print(f"  autorizada e não observada ({regra['finding']}): "
                  f"{regra['request']} {regra['key']} — a correção autorizada "
                  f"no portão não produziu a mudança declarada")
        return 1

    distintos = len({r["status"] for r in base})
    if distintos == 1:
        print(
            f"ATENÇÃO: as {len(base)} requisições devolveram todas o mesmo "
            f"status {base[0]['status']}. Conferir o passo 1.6 antes de "
            "confiar neste resultado."
        )

    print(f"APROVADO: {len(base)} requisições, "
          f"{len(autorizadas)} divergência(s) autorizada(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
