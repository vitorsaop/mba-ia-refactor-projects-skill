# Playbook de refatoração

## Conteúdo

- Como usar o playbook
- Ordem de aplicação
- T1 a T15: transformações do grupo 2, aplicadas por padrão
- T16 a T18 e T22: transformações do grupo 3, que alteram o contrato
- T19 a T21 e T23: transformações do grupo 2, complementares
- Tabela de correspondência anti-pattern para transformação
- Tradução do campo `Mudança de contrato:` para `expected.json`

## Como usar o playbook

Cada transformação tem: o gatilho, o par antes/depois, e a verificação que
comprova a preservação de comportamento.

Regras:

1. Uma transformação por vez. Não misturar movimentação de arquivo com mudança
   de lógica no mesmo passo.
2. Cada bloco `Antes` é um padrão observado; cada bloco `Depois` é o alvo. Os
   nomes de arquivo dos exemplos seguem a convenção de
   `mvc-architecture.md`.
3. **A verificação de cada transformação é obrigatória e registrada.** O bloco
   `Verificação` não é comentário: ao concluir a transformação, executá-lo e
   gravar o resultado na coluna `Evidência` do registro de remediação.
   Transformação sem verificação executada não recebe o destino `CORRIGIDA`.
   Transformação sem bloco `Verificação` é defeito deste playbook, nunca licença
   para registrar `CORRIGIDA` sem evidência.
4. Transformações do grupo 3 só são aplicadas quando autorizadas no portão da
   Fase 2.
5. **O grupo de uma correção é decidido na Fase 2, não aqui.** Se ao detalhar a
   transformação ficar claro que ela altera o contrato e a Fase 2 não a
   classificou assim, isso é reclassificação: parar, registrar e voltar ao
   usuário com um portão estreito, conforme `remediation-protocol.md`.
   Descartar a correção com base na própria reclassificação não é permitido.
6. **Correção autorizada que altera o contrato vira entrada em
   `expected.json`,** escrita antes de editar o código. O campo `Mudança de
   contrato:` da constatação é a fonte. Sem a entrada, a validação reprova a
   mudança que o próprio usuário autorizou. Com a entrada, a validação passa a
   exigir que a mudança realmente ocorra.
7. **Uma transformação cujo padrão prescrito preserva a condição insegura fecha
   como `MITIGADA`, não como `CORRIGIDA`.** O caso típico é T19. O residual e o
   que o encerra são declarados no registro e reaparecem em `## Risco residual`.

## Ordem de aplicação

A ordem reduz retrabalho. Estrutura primeiro, lógica depois.

```
1. Estrutura      T2, T3, T4, T15   criar camadas e mover código
2. Correção       T1, T6, T9, T14   segurança e integridade
3. Consolidação   T5, T10, T11, T13 mover regra e remover duplicação
4. Desempenho     T7, T8            reduzir idas ao banco e linearizar fluxo
5. Limpeza        T12, T19, T20, T21, T23
6. Autorizadas    T16, T17, T18, T22
```

---

## T1 — Consulta concatenada para consulta parametrizada

**Gatilho.** C1.

### Antes

```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

cursor.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES ('" +
    nome + "', '" + descricao + "', " + str(preco) + ", " + str(estoque) + ", '" + categoria + "')"
)
```

### Depois

```python
conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))

conn.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
    "VALUES (?, ?, ?, ?, ?)",
    (nome, descricao, preco, estoque, categoria),
)
```

### Filtro montado de forma incremental

```python
# Antes
query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
if categoria:
    query += " AND categoria = '" + categoria + "'"
cursor.execute(query)
```

```python
# Depois
clausulas = ["1=1"]
parametros = []
if termo:
    clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
    parametros.extend([f"%{termo}%", f"%{termo}%"])
if categoria:
    clausulas.append("categoria = ?")
    parametros.append(categoria)
conn.execute("SELECT * FROM produtos WHERE " + " AND ".join(clausulas), parametros)
```

Apenas nomes de coluna e operadores continuam vindo de literal do código. Todo
valor vai como parâmetro.

**Verificação.** Para entrada legítima, o conjunto de linhas devolvido é
idêntico. Testar também um valor com apóstrofo, que antes quebrava a consulta e
agora é tratado como texto.

---

## T2 — Segredo e sinalizador embutido para módulo de configuração

**Gatilho.** C2, C8.

### Antes

```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

### Classificar cada valor antes de mover

Mover o segredo para outro arquivo não resolve C2. Enquanto o literal existir no
código-fonte, ele continua no histórico de versionamento e continua exigindo
alteração de código para ser rotacionado, que é exatamente o impacto descrito em
C2. Classificar cada valor em uma das três categorias:

| Categoria | Exemplos | O que fazer com o literal atual |
|---|---|---|
| A. Não secreto | caminho do banco, porta, nível de log, origens permitidas | Manter como valor padrão. Não é segredo, e o padrão preserva o boot. |
| B. Segredo sem verificação externa | chave de assinatura de sessão que o projeto não usa para assinar nada | Remover do código. Gerar em tempo de execução quando a variável estiver ausente. |
| C. Segredo com verificação externa | chave de gateway de pagamento, senha de SMTP, senha de banco | Remover do código. Sem valor padrão. Falhar com mensagem clara no momento do uso. |

Para decidir entre B e C, buscar onde o valor é efetivamente consumido. Um
segredo cujo único consumidor é código morto pertence à categoria C e sai junto
com o código morto, por T12.

### Depois

```python
# src/config/settings.py
import os
import secrets

# Categoria A: o literal atual vira o padrão. Host e porta saem do código de
# boot para cá com o mesmo valor, para que o comando documentado não mude.
DB_PATH = os.getenv("DB_PATH", "loja.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

# Categoria B: sem literal no código. Ausente a variável, gera-se por boot.
# Verificado antes de aplicar: o projeto não usa `session`, `flash` nem
# assinatura, portanto uma chave distinta por boot não altera nada observável.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)


# Categoria C: sem literal e sem padrão. Falha no uso, não no import.
def require(nome):
    valor = os.getenv(nome)
    if not valor:
        raise RuntimeError(
            f"variável de ambiente {nome} não definida. "
            f"Copiar .env.example para .env e preencher."
        )
    return valor
```

```python
# src/app.py
from src.config import settings

app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
```

Criar `.env.example` na raiz do projeto, versionado, com as chaves e sem os
valores. Acrescentar `.env` ao `.gitignore`.

```
# .env.example
DB_PATH=loja.db
DEBUG=false
HOST=0.0.0.0
PORT=5000
CORS_ORIGINS=*
SECRET_KEY=
PAYMENT_GATEWAY_KEY=
SMTP_PASSWORD=
```

**Antes de mover um valor para a categoria B, confirmar que ele não assina
nada.** Se o projeto usar `session`, `flash`, cookies assinados ou tokens
assinados, uma chave nova por boot invalida o que já foi emitido, o que é uma
mudança de comportamento do grupo 3. Nesse caso o valor é da categoria C.

### Varredura de resíduo, obrigatória ao concluir T2

Mover o segredo para o módulo de configuração não encerra C2. O literal costuma
existir em mais de um ponto: uma resposta de verificação de saúde que devolve o
valor, um comentário, um arquivo de exemplo, um artefato de carga inicial, um
teste. Corrigir a atribuição e declarar a constatação resolvida é a correção
parcial mais comum desta transformação, e já aconteceu em execução real.

Para cada literal original:

A busca corre sobre o **escopo de código-fonte do projeto** definido em
`stack-detection.md`. Isso não é detalhe: sem excluir `reports/` e o diretório da
própria skill, a busca reencontra os literais de exemplo que esta referência e o
catálogo trazem, e o trecho citado no relatório da Fase 2. Medido em um projeto
real, o mesmo literal devolve cinco ocorrências sem o escopo e uma com ele.

```bash
grep -rn --binary-files=without-match -F "<literal original>" . \
  --exclude-dir=.git --exclude-dir=.refactor-arch --exclude-dir=reports \
  --exclude-dir=node_modules --exclude-dir=__pycache__ \
  --exclude-dir=.claude
```

O último `--exclude-dir` é o diretório da skill, cujo nome segue a convenção da
ferramenta em uso. A busca é textual e por isso independe de linguagem e de
framework.

Leitura do resultado, sempre contra o registro de remediação:

| Resultado | Significado |
|---|---|
| zero ocorrências | a localização fecha como `CORRIGIDA` |
| ocorrência em linha cujo destino é `NÃO APLICADA` | esperado: aquela correção foi declinada no portão |
| ocorrência em qualquer outro lugar | correção parcial: a localização não fecha |

Ocorrência encontrada fora das localizações já listadas é acrescentada à
constatação existente e ganha linha no registro. Ela não vira constatação nova.

Gravar o número de ocorrências de cada literal na coluna `Evidência`.

**Verificação.**

1. A aplicação sobe sem nenhuma variável de ambiente definida.
2. A varredura de resíduo acima devolve zero ocorrências fora das linhas
   declaradas `NÃO APLICADA`.
3. Os endpoints devolvem o mesmo corpo da linha de base.
4. Uma exceção não tratada passa a devolver o corpo do tratador central em vez
   do rastreamento, porque o modo de depuração passou a ser desligado por
   padrão. Isso não altera as respostas das rotas existentes.

---

## T3 — Módulo multi-responsabilidade para módulos por domínio

**Gatilho.** C7, SRP.

### Antes

```
models.py     314 linhas, domínios produto, usuário, pedido e relatório
controllers.py 292 linhas, os mesmos quatro domínios
```

### Depois

```
src/models/
├── produto_model.py
├── usuario_model.py
├── pedido_model.py
└── relatorio_model.py
src/controllers/
├── produto_controller.py
├── usuario_controller.py
├── pedido_controller.py
└── relatorio_controller.py
```

Procedimento:

1. Agrupar as funções por substantivo de domínio.
2. Criar um arquivo por grupo, movendo as funções sem alterar o corpo.
3. Resolver as importações entre módulos de domínio.
4. Só depois aplicar as transformações de lógica.

**Verificação.** Nenhuma função perdida. A contagem de funções antes e depois é
igual. Os endpoints respondem como na linha de base.

---

## T4 — Registro de rota disperso para camada de rotas

**Gatilho.** H2.

### Antes

```python
# app.py, misturado com configuração e handlers
app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])

@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    ...
```

### Depois

```python
# src/views/routes.py
from flask import Blueprint
from src.controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)
produto_bp.add_url_rule("/produtos", "listar_produtos",
                        produto_controller.listar, methods=["GET"])
```

```javascript
// src/routes/index.js
const { Router } = require('express');

module.exports = ({ checkoutController }) => {
    const router = Router();
    router.post('/api/checkout', checkoutController.handle);
    return router;
};
```

Nenhum handler é definido no arquivo de rotas. O arquivo contém apenas
associações.

**Verificação.** O inventário de rotas da Fase 1 é reproduzido integralmente:
mesmo caminho, mesmo método, mesma quantidade.

---

## T5 — Regra de negócio no handler para o model

**Gatilho.** H1, H2.

### Antes

```python
@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    all_tasks = Task.query.all()
    overdue_count = 0
    for t in all_tasks:
        if t.due_date:
            if t.due_date < datetime.utcnow():
                if t.status != 'done' and t.status != 'cancelled':
                    overdue_count = overdue_count + 1
```

### Depois

```python
# src/models/task_model.py
def count_overdue():
    tasks = db.session.execute(db.select(Task)).scalars().all()
    return sum(1 for task in tasks if task.is_overdue())
```

```python
# src/controllers/task_controller.py
def stats():
    return jsonify(task_model.build_stats()), 200
```

O handler passa a ter uma chamada e uma montagem de resposta.

**Verificação.** O valor de `overdue` no corpo da resposta é o mesmo da linha de
base para o mesmo conjunto de dados.

---

## T6 — Conexão global e instanciação concreta para fábrica injetada

**Gatilho.** H3, H4, DIP.

### Antes, Python

```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
        db_connection.row_factory = sqlite3.Row
    return db_connection
```

### Depois, Python

```python
# src/config/database.py
import sqlite3
from contextlib import contextmanager
from src.config.settings import DB_PATH


@contextmanager
def get_connection(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### Antes, Node.js

```javascript
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
}
```

### Depois, Node.js

```javascript
// src/container.js
module.exports = (settings) => {
    const db = wrap(new sqlite3.Database(settings.dbFile));
    return { db, courseModel: new CourseModel(db), paymentModel: new PaymentModel(db) };
};
```

Atenção com banco em memória: cada conexão nova cria um banco vazio. Quando o
projeto usa `:memory:`, a instância única deve ser criada uma vez no container e
compartilhada, e a transformação consiste em remover a instanciação de dentro da
classe de política, não em abrir uma conexão por operação.

**Verificação.** A aplicação sobe, o esquema é criado e os dados de carga
inicial estão presentes. Os endpoints de leitura devolvem os mesmos registros.

---

## T7 — Consulta em laço para consulta única

**Gatilho.** M1.

### Antes

```python
for row in rows:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

### Depois

```python
SQL_ITENS = """
    SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
           p.nome AS produto_nome
    FROM itens_pedido ip
    LEFT JOIN produtos p ON p.id = ip.produto_id
    WHERE ip.pedido_id IN ({placeholders})
"""


def _itens_por_pedido(conn, pedido_ids):
    if not pedido_ids:
        return {}
    placeholders = ",".join("?" for _ in pedido_ids)
    linhas = conn.execute(
        SQL_ITENS.format(placeholders=placeholders), pedido_ids
    ).fetchall()
    agrupado = {pid: [] for pid in pedido_ids}
    for linha in linhas:
        agrupado[linha["pedido_id"]].append({
            "produto_id": linha["produto_id"],
            "produto_nome": linha["produto_nome"] or "Desconhecido",
            "quantidade": linha["quantidade"],
            "preco_unitario": linha["preco_unitario"],
        })
    return agrupado
```

`LEFT JOIN` e o valor de reserva `"Desconhecido"` preservam o comportamento
original para produto removido.

Em ORM, o equivalente é carga antecipada:

```python
db.select(Task).options(db.joinedload(Task.user), db.joinedload(Task.category))
```

**Verificação.** A lista devolvida tem os mesmos elementos, na mesma ordem, com
as mesmas chaves. Confirmar o caso de produto ausente.

---

## T8 — Callbacks aninhados para fluxo linear

**Gatilho.** H5.

### Antes

```javascript
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    if (err || !course) return res.status(404).send("Curso não encontrado");
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        this.db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
            let enrId = this.lastID;
            self.db.run("INSERT INTO payments ...", [...], function (err) { ... });
        });
    });
});
```

### Depois

```javascript
// src/config/db.js - adaptador de promessa sobre o driver de callback
const wrap = (db) => ({
    get: (sql, params = []) => new Promise((resolve, reject) =>
        db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)))),
    all: (sql, params = []) => new Promise((resolve, reject) =>
        db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)))),
    run: (sql, params = []) => new Promise((resolve, reject) =>
        db.run(sql, params, function (err) {
            return err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes });
        })),
});
```

O `run` usa `function` em vez de arrow function porque `this.lastID` é fornecido
pelo driver no contexto do callback.

```javascript
// src/controllers/checkoutController.js
const course = await this.courseModel.findActiveById(courseId);
if (!course) return res.status(404).send('Curso não encontrado');

const userId = await this.userModel.findOrCreateByEmail(eml, usr, pwd);
const enrollmentId = await this.enrollmentModel.create(userId, courseId);
await this.paymentModel.record(enrollmentId, course.price, status);
```

**Verificação.** Os códigos 200, 400 e 404 e o corpo com as chaves `msg` e
`enrollment_id` são idênticos. Confirmar que o caminho de erro devolve uma única
resposta.

---

## T9 — Escrita em múltiplos passos para transação

**Gatilho.** H6.

### Antes

```python
cursor.execute("INSERT INTO pedidos ...")
pedido_id = cursor.lastrowid
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()
```

### Depois

```python
def criar_pedido(usuario_id, itens):
    with get_connection() as conn:          # commit no sucesso, rollback no erro
        total = _calcular_total(conn, itens)
        cursor = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid
        for item in itens:
            preco = _preco_atual(conn, item["produto_id"])
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], preco),
            )
            conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
    return {"pedido_id": pedido_id, "total": total}
```

Em Node.js com SQLite, o equivalente é envolver a sequência em
`BEGIN` e `COMMIT`, com `ROLLBACK` no bloco de erro.

**Verificação.** O pedido criado com sucesso tem o mesmo identificador e total.
Forçar falha no meio da sequência e confirmar que nenhuma linha permanece.

---

## T10 — Lógica duplicada para função única

**Gatilho.** M2.

### Antes

O mesmo bloco em cinco handlers:

```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
        else:
            task_data['overdue'] = False
    else:
        task_data['overdue'] = False
else:
    task_data['overdue'] = False
```

com o método já definido e não usado:

```python
class Task(db.Model):
    def is_overdue(self): ...
```

### Depois

```python
# src/models/task_model.py
class Task(db.Model):
    def is_overdue(self):
        if not self.due_date:
            return False
        if self.due_date >= datetime.now(timezone.utc).replace(tzinfo=None):
            return False
        return self.status not in TERMINAL_STATUSES

    def to_dict(self):
        data = { ... }
        data['overdue'] = self.is_overdue()
        return data
```

```python
# nos cinco pontos anteriores
task_data['overdue'] = t.is_overdue()
```

Quando o método já existe, reusá-lo em vez de criar outro. Duas implementações
da mesma regra é o problema que a transformação resolve.

**Verificação.** O valor de `overdue` é idêntico ao da linha de base nos cinco
endpoints, inclusive para tarefa sem data, tarefa vencida concluída e tarefa
vencida cancelada.

---

## T11 — Tratamento de erro por handler para tratador centralizado

**Gatilho.** H7, M4.

### Antes

```python
def listar_produtos():
    try:
        produtos = models.get_todos_produtos()
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"erro": str(e)}), 500
```

### Depois

```python
# src/middlewares/error_handler.py
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register(app):
    @app.errorhandler(Exception)
    def handle(exc):
        if isinstance(exc, HTTPException):
            return exc          # preserva 404 de rota inexistente, 405 e demais
        logger.exception("erro não tratado")
        return jsonify({"erro": str(exc)}), 500
```

```python
# src/controllers/produto_controller.py
def listar():
    return jsonify({"dados": produto_model.get_all(), "sucesso": True}), 200
```

O corpo `{"erro": str(exc)}` e o código 500 são os mesmos que os blocos
individuais produziam.

**A guarda `isinstance(exc, HTTPException)` é obrigatória.** Um tratador
registrado para `Exception` também casa com as exceções de HTTP do roteamento,
porque o Flask percorre a hierarquia de classes da exceção ao procurar o
tratador. Sem a guarda, um caminho inexistente passa a devolver 500 em vez de
404, e um método não permitido passa a devolver 500 em vez de 405. Isso viola a
regra permanente 4. Medido em Flask 3.1.1:

| Requisição | Sem tratador | Tratador sem guarda | Tratador com guarda |
|---|---|---|---|
| `GET /naoexiste` | 404 | 500 | 404 |
| `POST` em rota só de `GET` | 405 | 500 | 405 |
| `GET /produtos/1` | 200 | 200 | 200 |

`werkzeug` já é dependência do Flask, portanto a importação não viola a regra
permanente 7.

Para `except:` sem tipo, a correção é remover o bloco e deixar a exceção subir
ao tratador. Quando o bloco existe para converter erro em código específico,
manter o bloco e nomear o tipo:

```python
    except EstoqueInsuficiente as exc:
        return jsonify({"erro": str(exc), "sucesso": False}), 400
```

Em Express, o tratador é o último middleware registrado, com quatro parâmetros:

```javascript
app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).send('Erro interno');
});
```

**Verificação.** Provocar uma exceção e confirmar o mesmo código de status e o
mesmo corpo da linha de base. Sondar também um caminho fora do inventário de
rotas e um método não permitido em rota existente, confirmando 404 e 405 iguais
aos da linha de base.

---

## T12 — Remoção de código morto e importação não utilizada

**Gatilho.** M5.

### Antes

```python
import os, sys, json, datetime          # apenas datetime é usado
from utils.helpers import format_date, calculate_percentage   # nenhuma é chamada
```

### Depois

```python
import datetime
```

Procedimento para módulo inteiro sem referência:

1. Buscar o nome do símbolo em todo o projeto.
2. Confirmar zero referência fora da própria definição.
3. Remover.

Quando o módulo não usado contém funcionalidade que deveria estar ativa, como
um serviço de notificação nunca importado, isso é uma constatação separada de
funcionalidade ausente. Reportar; não ativar por conta própria, porque ativar
altera comportamento.

**Verificação.** A aplicação importa e sobe. Nenhum `ImportError` ou
`ReferenceError`.

---

## T13 — Número mágico e literal repetido para constante nomeada

**Gatilho.** L1, L5, OCP.

### Antes

```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
```

```python
valid = ['pending', 'in_progress', 'done', 'cancelled']   # repetido em 4 arquivos
```

### Depois

```python
# src/config/settings.py
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
VALID_TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
TERMINAL_STATUSES = ("done", "cancelled")
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
```

```python
from src.config.settings import FAIXAS_DESCONTO


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0
```

Os valores permanecem os mesmos. Se o projeto já define constantes em um módulo
de apoio que ninguém importa, reusá-las em vez de criar novas.

**Verificação.** Para uma amostra de valores em cada faixa e nos limites exatos,
o resultado é idêntico ao da linha de base. Testar `faturamento == 10000`, que
cai na faixa seguinte tanto antes quanto depois.

---

## T14 — API obsoleta para substituto oficial

**Gatilho.** M6. Tabela em `deprecated-apis.md`.

### Antes

```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
task = Task.query.get(task_id)
tasks = Task.query.filter_by(status='done').all()
```

### Depois

```python
def _utcnow_naive():
    """Substitui datetime.utcnow preservando o valor sem fuso persistido."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


created_at = db.Column(db.DateTime, default=_utcnow_naive)
task = db.session.get(Task, task_id)
tasks = db.session.execute(
    db.select(Task).where(Task.status == 'done')
).scalars().all()
```

`replace(tzinfo=None)` é necessário quando as colunas persistem valores sem
fuso. Sem essa chamada, comparar o novo valor com valores já gravados levanta
`TypeError`.

### Node.js

```javascript
// Antes
const buf = new Buffer(pwd);
const parsed = url.parse(req.url);

// Depois
const buf = Buffer.from(pwd);
const parsed = new URL(req.url, `http://${req.headers.host}`);
```

**Verificação.** Os campos de data no corpo da resposta têm o mesmo formato. As
consultas devolvem o mesmo conjunto de registros.

---

## T15 — Ponto de entrada com regras para composition root

**Gatilho.** C7.

### Antes

```python
# app.py: configuração, rotas, dois handlers com SQL, e o boot
app = Flask(__name__)
app.config["SECRET_KEY"] = "..."
app.add_url_rule(...)

@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json().get("sql", ""))
```

### Depois

```python
# src/app.py
def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    error_handler.register(app)
    return app
```

```python
# app.py na raiz, nome preservado
from src.app import create_app
from src.config import settings

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

O host, a porta e o sinalizador de depuração saem do módulo de configuração,
como T2 categoria A prescreve, com **padrão igual ao literal que o projeto já
tinha**. O `5000` dos exemplos é o valor do projeto de referência: o padrão
gravado é sempre o valor observado no código de boot do próprio projeto, e por
isso o comando documentado continua funcionando sem nenhuma variável definida.

Para que a validação exercite o padrão, e não o ambiente de quem executa, as
duas capturas sobem a aplicação com essas variáveis desdefinidas
(`env -u PORT -u DEBUG ... <comando de boot>`). Variável que precise estar
definida é registrada em `.refactor-arch/runtime.md` com o valor usado.

O arquivo da raiz mantém o nome e os símbolos exportados, então o comando de
boot documentado e scripts que importam de `app` continuam funcionando.

**Verificação.** O comando de boot do README executa sem alteração. Scripts
auxiliares importam os mesmos símbolos.

---

## T16 — Endpoint perigoso: remoção ou proteção

**Gatilho.** C3, C4. **Grupo 3, altera o contrato.**

Duas opções. Escolher pela resposta do usuário no portão.

### Opção A, remoção

Remover a rota. O endpoint deixa de existir e passa a devolver 404.

### Opção B, proteção

```python
# src/middlewares/admin_guard.py
import hmac
from functools import wraps
from flask import request, jsonify
from src.config.settings import ADMIN_TOKEN


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        enviado = request.headers.get("X-Admin-Token", "")
        if not ADMIN_TOKEN or not hmac.compare_digest(enviado, ADMIN_TOKEN):
            return jsonify({"erro": "Não autorizado"}), 401
        return view(*args, **kwargs)
    return wrapper
```

### Opção recomendada por gatilho

O item do portão só consegue apresentar uma opção como padrão, então a
recomendação é declarada aqui e nomeada no texto do item.

| Gatilho | Recomendada | Motivo |
|---|---|---|
| C3, comando arbitrário | Opção A, remoção | proteger por token não remove a capacidade de executar comando arbitrário; quem tiver a credencial continua com a conta de banco inteira |
| C4, destrutivo sem autenticação | Opção B, proteção | a operação tem uso operacional legítimo, e a proteção elimina o acesso anônimo sem remover a função |

Um número nu no portão seleciona a opção recomendada. As formas `<n>a` e `<n>b`
selecionam explicitamente. Ver `remediation-protocol.md`, "Autorização no
portão".

**Mudança de contrato.** Opção A remove o endpoint. Opção B acrescenta a
resposta de recusa para requisição sem credencial.

**Verificação.**

- Opção A: a rota alvo passa a responder o código que o framework devolve para
  caminho não registrado. Registrar o código observado, sem presumir 404 nem
  405, porque isso varia por framework. Toda outra entrada de `baseline.json`
  permanece idêntica. A entrada correspondente em `expected.json` foi declarada
  e observada.
- Opção B: sem credencial, o status passa a ser o de recusa e o corpo é o do
  tratador. Com credencial válida, corpo e status idênticos aos da linha de
  base.

---

## T17 — Senha em texto puro ou digest fraco para digest com sal

**Gatilho.** C5. **Grupo 3, altera o contrato.**

### Antes

```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

### Depois, sem acrescentar dependência

```python
import hashlib
import hmac
import os

ITERACOES = 240000     # custo de derivação; valor único em src/config/settings.py
ALGORITMO = "sha256"
TAMANHO_SAL = 16


def hash_password(pwd):
    sal = os.urandom(TAMANHO_SAL)
    digest = hashlib.pbkdf2_hmac(ALGORITMO, pwd.encode(), sal, ITERACOES)
    return f"pbkdf2_{ALGORITMO}${ITERACOES}${sal.hex()}${digest.hex()}"


def verify_password(pwd, armazenado):
    try:
        _, iteracoes, sal_hex, digest_hex = armazenado.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        ALGORITMO, pwd.encode(), bytes.fromhex(sal_hex), int(iteracoes)
    )
    return hmac.compare_digest(digest.hex(), digest_hex)
```

`pbkdf2_hmac` e `compare_digest` são da biblioteca padrão, portanto a
transformação não introduz dependência nova.

**Mudança de contrato.** As senhas já persistidas deixam de validar. O script de
carga inicial precisa ser executado novamente. Registrar essa exigência no bloco
`## Não aplicadas` quando a transformação não for autorizada.

**Verificação.** Nenhum digest no formato antigo permanece no artefato de carga
inicial: contar por busca textual dentro do escopo de código-fonte definido em
`stack-detection.md`.

Atenção ao que o protocolo de validação impõe: as duas capturas partem do mesmo
`.refactor-arch/db.snapshot`. Quando o instantâneo contém senhas no formato
antigo, a autenticação passa a falhar depois desta transformação. **Essa
divergência é a divergência autorizada da constatação**: ela é declarada em
`expected.json` e não é "corrigida" no código. Quando a mudança não aparece na
captura, por exemplo porque o endpoint que expunha a senha também foi corrigido,
a entrada se declara `"observable": false` e esta verificação é a que a
substitui. Regenerar a carga inicial é ação posterior de quem executa,
registrada na coluna `Evidência`.

---

## T18 — Dado sensível na resposta para resposta reduzida

**Gatilho.** C6. **Grupo 3, altera o contrato.**

### Antes

```python
def to_dict(self):
    return {'id': self.id, 'name': self.name, 'email': self.email,
            'password': self.password, 'role': self.role}
```

### Depois

```python
def to_public_dict(self):
    return {'id': self.id, 'name': self.name, 'email': self.email,
            'role': self.role}
```

Aplicar também ao endpoint de verificação de saúde, removendo as chaves de
configuração interna.

**Mudança de contrato.** A chave sai do corpo da resposta em todos os endpoints
que usavam a serialização. Listar cada endpoint afetado no campo `Mudança de
contrato:` da constatação.

**Verificação.** As chaves nomeadas em `Mudança de contrato:` estão ausentes do
corpo em todos os endpoints afetados. Todas as demais chaves, em todos os
endpoints, permanecem idênticas à linha de base. Cada endpoint afetado tem
entrada em `expected.json`, e cada entrada foi observada.

---

## T19 — Política de origem cruzada aberta para lista configurável

**Gatilho.** H8.

### Antes

```python
CORS(app)
```

### Depois

```python
# src/config/settings.py
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
```

```python
CORS(app, origins=settings.CORS_ORIGINS)
```

O padrão aberto preserva o comportamento atual. A política passa a ser
configurável sem alterar código.

### Destino desta transformação

Preservar o comportamento atual é preservar a política aberta: depois de T19 a
origem cruzada continua liberada até que alguém defina a variável. O achado de
segurança descrito em H8 não deixou de existir; ele passou a ser desligável.

Por isso T19 aplicada com padrão aberto fecha a constatação como `MITIGADA`,
nunca como `CORRIGIDA`. O residual declarado é "qualquer origem continua aceita
enquanto a variável não for definida", e o que fecha é definir a lista de
origens no ambiente de execução.

Quando o usuário quiser fechar de fato dentro da refatoração, a alternativa é
adotar uma lista restritiva como padrão. Isso altera o cabeçalho de resposta
para origens hoje aceitas, portanto é do grupo 3: precisa constar como
`[altera-contrato]` já na Fase 2 e ser autorizada no portão.

A mesma regra vale para qualquer transformação cujo padrão prescrito preserve a
condição insegura descrita na constatação.

**Verificação.** Sem variável de ambiente definida, o cabeçalho de resposta é o
mesmo da linha de base. O destino registrado é `MITIGADA`, com o residual
descrito.

---

## T20 — Validação ausente para validação no controller

**Gatilho.** M3.

### Antes

```python
category.color = data.get('color', '#000000')
```

com a verificação disponível e não chamada:

```python
def is_valid_color(color):
    if color and len(color) == 7 and color[0] == '#':
        return True
    return False
```

### Depois

```python
# src/controllers/category_controller.py
def create():
    data = request.get_json() or {}
    cor = data.get('color', DEFAULT_COLOR)
    if not is_valid_color(cor):
        return jsonify({'error': 'Cor inválida'}), 400
    ...
```

Acrescentar validação cria uma resposta 400 que antes não existia para entrada
inválida. Entrada válida continua produzindo o mesmo resultado.

### O grupo desta transformação é decidido na Fase 2

Quando a validação nova recusa entrada que antes era aceita e persistida, a
mudança é do grupo 3. Essa frase está correta, mas decidi-la durante a Fase 3 é
tarde: nesse ponto o portão já passou, e a única saída aparente vira descartar a
correção. Foi assim que uma constatação de validação incompleta desapareceu de
uma execução real, reclassificada dentro do plano e nunca aplicada.

Procedimento correto, na Fase 2, ao registrar uma constatação de validação
ausente ou incompleta:

1. Ler o caminho de escrita e determinar se existe entrada hoje aceita e
   persistida que a validação nova passaria a recusar.
2. Se existir, a constatação já sai do relatório com a marca
   `[altera-contrato]` e o campo `Mudança de contrato:` descrevendo qual
   entrada passa de aceita a recusada, e entra na lista do portão.
3. Se não existir, isto é, se a validação nova só recusa o que já falhava
   adiante, a constatação é do grupo 2 e é aplicada por padrão.

O caso mais comum do item 2 é a validação de campo acrescentada a uma rota de
atualização que hoje aceita qualquer valor.

**Verificação.** Entrada válida produz o mesmo corpo e o mesmo código de status.
Entrada inválida passa a produzir 400 em vez de persistir valor inconsistente.
Quando a constatação foi autorizada como `[altera-contrato]`, a nova resposta
400 está declarada em `expected.json`.

---

## T21 — Renomeação de identificador

**Gatilho.** L2.

### Antes

```javascript
let u = req.body.usr;
let e = req.body.eml;
let cid = req.body.c_id;
let cc = req.body.card;
```

### Depois

```javascript
const { usr: userName, eml: email, c_id: courseId, card: cardNumber } = req.body;
```

As chaves do corpo da requisição, `usr`, `eml`, `c_id` e `card`, não mudam.
Renomear apenas a variável local. Alterar o nome da chave é mudança de contrato.

Em Python, renomear parâmetro que sombreia identificador embutido:

```python
def buscar_produto(id):          # antes
def buscar_produto(produto_id):  # depois
```

Quando o parâmetro vem de um conversor de rota, o nome precisa acompanhar a
declaração da rota:

```python
app.add_url_rule("/produtos/<int:produto_id>", ...)
```

**Verificação.** O caminho da rota e o formato do corpo aceito são idênticos.

---

## T22 — Padronização de envelope de resposta

**Gatilho.** L4. **Grupo 3, altera o contrato.**

### Antes

```python
return jsonify(result), 200                              # lista sem envelope
return jsonify({'error': 'Task não encontrada'}), 404    # erro com objeto
```

### Depois

```python
return jsonify({"dados": result, "sucesso": True}), 200
return jsonify({"erro": "Task não encontrada", "sucesso": False}), 404
```

**Mudança de contrato.** Todo cliente que hoje lê a lista diretamente passa a
precisar acessar a chave `dados`. Esta transformação só é aplicada com
autorização explícita, e a recomendação padrão é não aplicá-la, porque o ganho
é de padronização e o custo é quebra de todos os consumidores.

**Verificação.** Todo endpoint devolve o envelope declarado. Status e valores
internos idênticos à linha de base. Endpoint afetado sem entrada em
`expected.json` reprova.

---

## T23 — Saída em terminal para registro com nível

**Gatilho.** L3.

### Antes

```python
print("Produto criado com ID: " + str(id))
print("ERRO ao criar produto: " + str(e))
```

### Depois

```python
# src/config/logging_config.py
import logging


def configure(level="INFO"):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
```

```python
import logging

logger = logging.getLogger(__name__)

logger.info("produto criado id=%s", produto_id)
logger.exception("falha ao criar produto")
```

Em Node.js, sem acrescentar dependência, encapsular em um módulo próprio:

```javascript
// src/config/logger.js
const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const current = LEVELS[process.env.LOG_LEVEL || 'info'];

const log = (level, ...args) => {
    if (LEVELS[level] <= current) {
        console[level === 'debug' ? 'log' : level](`[${level.toUpperCase()}]`, ...args);
    }
};

module.exports = {
    error: (...a) => log('error', ...a),
    warn: (...a) => log('warn', ...a),
    info: (...a) => log('info', ...a),
    debug: (...a) => log('debug', ...a),
};
```

Ao aplicar T23, remover do conteúdo registrado qualquer dado sensível
identificado em C6. Número de cartão, senha e chave de gateway não vão para o
log em nenhum nível.

**Verificação.** A aplicação sobe e produz saída equivalente no nível
configurado. Nenhum dado sensível aparece na saída.

---

## Tabela de correspondência

| Anti-pattern | Transformação | Grupo |
|---|---|---|
| C1 SQL Injection | T1 | 2 |
| C2 Segredo embutido | T2 | 2 |
| C3 Comando arbitrário | T16 | 3 |
| C4 Destrutivo sem autenticação | T16 | 3 |
| C5 Senha em texto puro | T17 | 3 |
| C6 Dado sensível na resposta | T18 | 3 |
| C7 Módulo multi-responsabilidade | T3, T15 | 2 |
| C8 Depuração ativa | T2 | 2 |
| H1 Regra no handler | T5 | 2 |
| H2 Sem controller | T4, T5 | 2 |
| H3 Estado global | T6 | 2 |
| H4 Acoplamento concreto | T6 | 2 |
| H5 Callbacks aninhados | T8 | 2 |
| H6 Sem transação | T9 | 2 |
| H7 Exceção descartada | T11 | 2 |
| H8 Origem cruzada aberta | T19 | 2 |
| M1 Consulta em laço | T7 | 2 |
| M2 Lógica duplicada | T10 | 2 |
| M3 Validação ausente | T20 | 2 |
| M4 Erro não centralizado | T11 | 2 |
| M5 Código morto | T12 | 2 |
| M6 API obsoleta | T14 | 2 |
| L1 Número mágico | T13 | 2 |
| L2 Nome sem significado | T21 | 2 |
| L3 Saída em terminal | T23 | 2 |
| L4 Envelope inconsistente | T22 | 3 |
| L5 Literal repetido | T13 | 2 |

O grupo indicado nesta tabela é o padrão. Duas entradas mudam de grupo conforme
o projeto, e a decisão é da Fase 2, nunca da Fase 3:

| Entrada | Vira grupo 3 quando |
|---|---|
| M3 validação ausente, T20 | a validação nova recusa entrada hoje aceita e persistida |
| H8 origem cruzada, T19 | a correção adota lista restritiva como padrão em vez de preservar o padrão aberto |

---

## Tradução do campo `Mudança de contrato:` para `expected.json`

Toda correção autorizada no portão que altere o contrato precisa de entrada em
`.refactor-arch/expected.json`, escrita no passo 3.2, antes de editar o código.
A fonte é o campo `Mudança de contrato:` da constatação. O formato completo está
em `remediation-protocol.md`.

Exemplos de tradução:

| Mudança de contrato | Entradas |
|---|---|
| `GET /health` deixa de devolver `debug` e `secret_key` | duas entradas, `key` igual a `body.debug` e a `body.secret_key`, `kind` `removida` |
| `GET /usuarios` deixa de devolver `senha` | uma entrada, `key` igual a `body.dados[*].senha`, `kind` `removida` |
| `POST /admin/query` deixa de existir | uma entrada, `key` igual a `status`, `kind` `status` |
| `PUT /produtos/<id>` passa a devolver 400 para categoria inválida | uma entrada na requisição correspondente, `key` igual a `status`, `kind` `status` |
| a senha persistida passa a digest com sal | `"observable": false`, com a verificação declarada |

Uma correção autorizada cuja mudança não seja observável por HTTP declara
`"observable": false` e a verificação que a substitui. O comparador ignora essa
entrada; o registro de remediação exige que a verificação tenha sido executada e
que o resultado esteja na coluna `Evidência`.
