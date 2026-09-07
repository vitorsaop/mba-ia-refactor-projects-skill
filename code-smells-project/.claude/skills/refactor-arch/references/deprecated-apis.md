# APIs obsoletas: detecção e substituto oficial

## Conteúdo

- Procedimento de resolução
- Python, biblioteca padrão
- Python, SQLAlchemy e Flask-SQLAlchemy
- Python, Flask
- Node.js, biblioteca padrão
- Node.js, Express
- Como reportar
- Como estender a tabela

## Procedimento de resolução

Seguir os quatro passos. Não pular o passo 2.

1. **Buscar o símbolo** no código, usando a coluna `Símbolo` das tabelas
   abaixo.
2. **Resolver a versão**, por dois caminhos distintos conforme a origem da
   depreciação. As tabelas de biblioteca padrão têm chave em versão de
   linguagem, como `Python 3.12`, ou em identificador de depreciação do Node, e
   nenhum manifesto de dependências declara isso.

   **2a, depreciação de biblioteca.** Ler a versão declarada da dependência no
   arquivo de dependências do projeto.

   **2b, depreciação de linguagem ou runtime.** Ler de declaração explícita:
   `requires-python`, `python_requires`, `engines.node`, arquivo de versão como
   `.nvmrc` ou `.python-version`, diretiva `go` do `go.mod`.

3. **Aplicar a regra de supressão.** A constatação só é suprimida quando a
   declaração trouxer **limite superior estritamente anterior** à versão de
   depreciação.

   | Declaração | Símbolo depreciado em 3.12 | Resultado |
   |---|---|---|
   | `>=3.9,<3.11` | sim | suprime |
   | `>=3.9` | sim | **não suprime**: declara o mínimo suportado, não o runtime em uso |
   | nenhuma | sim | **não suprime**: a depreciação é propriedade da linguagem, não do projeto |

4. **Confirmar a ocorrência** abrindo o arquivo e registrando o intervalo de
   linhas.
5. **Reportar com o substituto nomeado.** Uma constatação de API obsoleta sem o
   substituto explícito está incompleta.

**A versão do interpretador ou runtime observado na máquina entra em
`Description:` como evidência, junto do comando usado para obtê-la, e nunca serve
para suprimir a constatação.** Suprimir com base no interpretador local faria o
mesmo código produzir relatórios opostos em duas máquinas. `Impact:` registra a
condição: a remoção ocorre a partir da versão de depreciação.

Regra de fonte: uma entrada só pertence a estas tabelas se a depreciação estiver
declarada na documentação oficial do fornecedor da biblioteca. Não incluir
entrada baseada em recomendação de terceiros.

## Python, biblioteca padrão

| Símbolo | Depreciado em | Substituto oficial | Severidade |
|---|---|---|---|
| `datetime.datetime.utcnow()` | Python 3.12 | `datetime.datetime.now(timezone.utc)` | MEDIUM |
| `datetime.datetime.utcfromtimestamp()` | Python 3.12 | `datetime.datetime.fromtimestamp(ts, timezone.utc)` | MEDIUM |

Nota sobre `utcnow`: o valor devolvido é ingênuo, sem fuso, enquanto o
substituto devolve valor com fuso. Ao aplicar T14, verificar as comparações
existentes. Comparar um valor com fuso e um valor sem fuso levanta `TypeError`.
Se o modelo persiste valores sem fuso, a substituição consistente é
`datetime.now(timezone.utc).replace(tzinfo=None)`, que preserva exatamente o
comportamento anterior e remove o símbolo obsoleto.

## Python, SQLAlchemy e Flask-SQLAlchemy

| Símbolo | Situação | Substituto oficial | Severidade |
|---|---|---|---|
| `Query.get(pk)` | Legado desde SQLAlchemy 2.0 | `Session.get(Model, pk)` | MEDIUM |
| `Model.query` | Interface legada em Flask-SQLAlchemy 3.1 | `db.session.execute(db.select(Model))` | MEDIUM |
| `Session.query()` | Interface legada em SQLAlchemy 2.0 | `Session.execute(select(...))` | MEDIUM |

Equivalências de tradução:

```python
# legado                              # moderno
Task.query.get(task_id)               db.session.get(Task, task_id)
Task.query.all()                      db.session.execute(db.select(Task)).scalars().all()
Task.query.filter_by(status='done')   db.select(Task).where(Task.status == 'done')
Task.query.count()                    db.session.execute(
                                          db.select(db.func.count()).select_from(Task)
                                      ).scalar()
Task.query.filter_by(x=1).first()     db.session.execute(
                                          db.select(Task).where(Task.x == 1)
                                      ).scalars().first()
```

Diferença de comportamento a verificar: `Query.get` devolve `None` quando o
registro não existe, e `Session.get` também. A tradução preserva o resultado.
Já `.scalars().all()` devolve lista, igual a `.all()`.

## Python, Flask

| Símbolo | Situação | Substituto oficial | Severidade |
|---|---|---|---|
| `flask.json.JSONEncoder` | Removido em Flask 2.3 | `app.json` com `DefaultJSONProvider` | MEDIUM |
| `@app.before_first_request` | Removido em Flask 2.3 | inicialização na fábrica da aplicação | MEDIUM |

## Node.js, biblioteca padrão

| Símbolo | Identificador | Tipo | Substituto oficial | Severidade |
|---|---|---|---|---|
| `new Buffer()` | DEP0005 | aplicação | `Buffer.from()`, `Buffer.alloc()`, `Buffer.allocUnsafe()` | MEDIUM |
| `url.parse()` | DEP0169, DEP0170 | runtime | `new URL()` da API WHATWG | MEDIUM |
| `crypto.createCipher()` | DEP0106 | fim de vida | `crypto.createCipheriv()` | HIGH |
| `crypto.createDecipher()` | DEP0106 | fim de vida | `crypto.createDecipheriv()` | HIGH |
| `util.isArray()` | DEP0044 | runtime | `Array.isArray()` | LOW |
| módulo `domain` | DEP0032 | documentação | sem substituto direto; usar `AsyncLocalStorage` | MEDIUM |

`crypto.createCipher` recebe severidade HIGH porque deriva a chave de forma
inadequada, além de estar em fim de vida.

## Node.js, Express

| Símbolo | Situação | Substituto oficial | Severidade |
|---|---|---|---|
| `bodyParser.json()` como dependência separada | embutido desde Express 4.16 | `express.json()` | LOW |
| `bodyParser.urlencoded()` como dependência separada | embutido desde Express 4.16 | `express.urlencoded()` | LOW |
| `app.del()` | removido em Express 4 | `app.delete()` | MEDIUM |
| `res.send(status, body)` | removido em Express 4 | `res.status(status).send(body)` | MEDIUM |
| `res.json(status, obj)` | removido em Express 4 | `res.status(status).json(obj)` | MEDIUM |

## Como reportar

A constatação segue o template de `audit-report-template.md`: rótulo em
inglês, conteúdo em português. Formato do campo `Description:` de uma
constatação de API obsoleta:

```
Description: <símbolo> está <depreciado desde <versão> | em situação legada> conforme a documentação oficial de <fornecedor>. O projeto declara <dependência>==<versão>. Ocorre <N> vezes neste arquivo.
Recommendation: Substituir por <substituto oficial>. Aplicar T14.
```

Exemplo preenchido:

```
### [MEDIUM] API obsoleta: datetime.utcnow() (F14, M6)
File: models/task.py:15-16
Description: `datetime.utcnow()` está depreciado desde Python 3.12 conforme a documentação oficial da biblioteca padrão. Ocorre 2 vezes neste arquivo, como valor padrão de coluna.
Impact: A remoção em versão futura quebra a criação de registros. O valor devolvido é ingênuo, o que já hoje impede comparação com valor com fuso.
Recommendation: Substituir por `datetime.now(timezone.utc)`. Se as colunas persistem valores sem fuso, usar `datetime.now(timezone.utc).replace(tzinfo=None)` para preservar o comportamento atual. Aplicar T14.
```

O símbolo obsoleto costuma aparecer em mais de um arquivo. Nesse caso a
constatação recebe o campo `Locations:` com todos eles, e o registro de
remediação abre uma linha por localização. Substituir o símbolo em um arquivo e
deixá-lo em outro é correção parcial, e a re-auditoria do passo 3.5 a detecta.

## Como estender a tabela

Ao encontrar um símbolo suspeito que não esteja nas tabelas:

1. Localizar a nota de depreciação na documentação oficial do fornecedor.
2. Se a nota existir, acrescentar linha à tabela da stack correspondente, com
   versão de depreciação e substituto exato.
3. Se a nota não existir, não reportar como API obsoleta. Avaliar contra o
   catálogo de anti-patterns; pode ser outra entrada.

Não registrar prazo, data futura, ou versão ainda não lançada nesta referência.
