# Catálogo de anti-patterns

## Conteúdo

- Como usar o catálogo
- Escala de severidade
- CRITICAL: C1 a C8
- HIGH: H1 a H8
- MEDIUM: M1 a M6
- LOW: L1 a L5
- Índice rápido de sinais

## Como usar o catálogo

Cada entrada tem cinco campos:

- **Sinal de detecção**: padrão buscável no código, independente de projeto.
- **Por que importa**: consequência verificável.
- **Severidade**: posição na escala.
- **Transformação**: identificador em `refactoring-playbook.md`.
- **Exemplo observado**: trecho real, para reconhecimento do padrão.

Regras:

1. Percorrer todas as 27 entradas. Não parar ao atingir cinco constatações.
2. Uma ocorrência só entra no relatório depois de o arquivo ser aberto e o
   intervalo de linhas confirmado.
3. Ocorrências repetidas do mesmo anti-pattern no mesmo arquivo são agrupadas em
   uma constatação, com todas as linhas listadas.
4. Ocorrências do mesmo anti-pattern em arquivos diferentes são constatações
   diferentes, cada uma com o seu próprio identificador `F`.
5. Exceção ao item 4: quando o mesmo defeito lógico tem ocorrências satélites
   que só fecham juntas, como um literal de segredo que precisa sair de todos os
   pontos onde aparece, a constatação pode ser única e listar todas as
   ocorrências no campo `Locations:`. Seja qual for a escolha, o invariante é
   o mesmo: o registro de remediação abre uma linha por localização, e nenhuma
   fecha sozinha.
6. O identificador do catálogo se repete entre constatações e por isso não
   identifica nenhuma delas. A chave única é o `F`, atribuído no passo 2.4. Ver
   `remediation-protocol.md`, "Identidade da constatação".
7. Os exemplos são material de reconhecimento. Não copiar caminho de arquivo do
   exemplo para o relatório.

## Escala de severidade

| Nível | Critério |
|---|---|
| CRITICAL | Falha de arquitetura ou segurança que impede o funcionamento correto, expõe dado sensível, ou viola completamente a separação de responsabilidades. |
| HIGH | Violação forte de MVC ou de princípio SOLID que dificulta muito manutenção e teste. |
| MEDIUM | Problema de padronização, duplicação, ou gargalo de desempenho moderado. |
| LOW | Legibilidade, nomenclatura, valor literal solto. |

---

## CRITICAL

### C1 — SQL Injection por concatenação

**Sinal de detecção.** Literal SQL unido a variável por operador de
concatenação, interpolação de string, ou template. Buscar `execute(` seguido de
`+`, de `f"`, de `%`, de `.format(`, ou de crase com `${`.

**Por que importa.** Entrada controlada pelo cliente altera a estrutura da
consulta. Permite leitura, alteração e remoção de dados fora do escopo do
endpoint.

**Severidade.** CRITICAL.

**Transformação.** T1.

**Exemplo observado.**

```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

Verificar também a montagem incremental de filtros:

```python
query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND (nome LIKE '%" + termo + "%')"
cursor.execute(query)
```

### C2 — Credencial ou segredo embutido no código

**Sinal de detecção.** Atribuição de literal a identificador que contenha
`secret`, `key`, `token`, `password`, `passwd`, `pass`, `pwd`, `credential`,
`api_key`. Inclui objetos de configuração literais e campos de conexão SMTP.

**Por que importa.** O segredo entra no histórico de versionamento e não pode
ser rotacionado sem alterar o código.

**Severidade.** CRITICAL.

**Transformação.** T2.

**Exemplo observado.**

```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

```javascript
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
};
```

```python
self.email_user = 'taskmanager@gmail.com'
self.email_password = 'senha123'
```

### C3 — Endpoint que executa comando arbitrário

**Sinal de detecção.** Handler de rota que passa conteúdo da requisição
diretamente para `execute`, `eval`, `exec`, `system`, ou equivalente.

**Por que importa.** Concede ao cliente a capacidade da conta de banco ou do
processo. Nenhuma validação de rota mitiga.

**Severidade.** CRITICAL.

**Transformação.** T16. Grupo 3, altera o contrato.

**Exemplo observado.**

```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)
```

### C4 — Operação destrutiva sem autenticação

**Sinal de detecção.** Handler que executa `DELETE FROM`, `DROP`, `TRUNCATE`, ou
remoção em massa, sem verificação de identidade ou de permissão no caminho de
execução.

**Por que importa.** Qualquer cliente com acesso de rede apaga os dados.

**Severidade.** CRITICAL.

**Transformação.** T16. Grupo 3, altera o contrato.

**Exemplo observado.**

```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
```

### C5 — Senha em texto puro ou digest inadequado

**Sinal de detecção.** Senha persistida sem transformação; uso de `md5`, `sha1`,
`base64`, ou função de embaralhamento escrita no próprio projeto; comparação de
senha por igualdade direta.

**Por que importa.** Digest rápido e sem sal permite recuperação por tabela
pré-computada. Codificação reversível não é digest.

**Severidade.** CRITICAL.

**Transformação.** T17. Grupo 3, altera o contrato, porque invalida
credenciais já persistidas.

**Exemplo observado.**

```python
cursor.executemany(
    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
    [("Admin", "admin@loja.com", "admin123", "admin")]
)
```

```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

```javascript
function badCrypto(pwd) {
    let hash = "";
    for (let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

No terceiro exemplo o laço produz sempre o mesmo par de caracteres, portanto o
resultado é a repetição de um valor derivado do início da senha. O custo de
10.000 iterações não acrescenta resistência.

### C6 — Dado sensível na resposta da API

**Sinal de detecção.** Dicionário ou objeto de resposta contendo chave de senha,
segredo, token, ou configuração interna. Verificar as funções de serialização e
o endpoint de verificação de saúde.

**Por que importa.** Expõe material de autenticação a qualquer cliente do
endpoint.

**Severidade.** CRITICAL.

**Transformação.** T18. Grupo 3, altera o contrato.

**Exemplo observado.**

```python
return jsonify({
    "status": "ok",
    "debug": True,
    "secret_key": "minha-chave-super-secreta-123"
}), 200
```

```python
def to_dict(self):
    return {'id': self.id, 'email': self.email, 'password': self.password}
```

### C7 — Módulo com múltiplas responsabilidades

**Sinal de detecção.** Um arquivo que contém, simultaneamente, ao menos três
entre: criação de esquema, consulta a banco, regra de negócio, definição de
rota, configuração, formatação de saída. Verificar também arquivos que cobrem
mais de um domínio.

**Por que importa.** Nenhuma parte pode ser exercitada em isolamento, e qualquer
alteração impacta domínios não relacionados.

**Severidade.** CRITICAL. Ver SRP em `solid-principles.md`.

**Transformação.** T3, T15.

**Exemplo observado.**

```javascript
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
    initDb() { this.db.run("CREATE TABLE users (...)"); }   // esquema e seed
    setupRoutes(app) {                                       // roteamento
        app.post('/api/checkout', (req, res) => {
            let status = cc.startsWith("4") ? "PAID" : "DENIED";   // regra
            this.db.run("INSERT INTO payments ...");                // persistência
        });
    }
}
```

### C8 — Modo de depuração ativo

**Sinal de detecção.** `debug=True`, `DEBUG = True`, `app.config["DEBUG"]`,
`NODE_ENV` ausente com stack trace exposta, sem condicionamento a variável de
ambiente.

**Por que importa.** Em Flask, o modo de depuração expõe um console interativo
de execução e o rastreamento completo da exceção ao cliente.

**Severidade.** CRITICAL.

**Transformação.** T2.

**Exemplo observado.**

```python
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```

---

## HIGH

### H1 — Regra de negócio dentro de rota ou controller

**Sinal de detecção.** Handler de rota contendo cálculo de domínio, comparação
de data para derivar estado, agregação, ou laço sobre entidades para computar
totais.

**Por que importa.** A regra não pode ser reutilizada nem exercitada sem
construir uma requisição HTTP.

**Severidade.** HIGH.

**Transformação.** T5.

**Exemplo observado.**

```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    for t in tasks:
        if t.due_date:
            if t.due_date < datetime.utcnow():
                if t.status != 'done' and t.status != 'cancelled':
                    task_data['overdue'] = True
```

Neste caso a regra já existe como método da entidade e não é usada. Ver M2.

### H2 — Camada de controller inexistente

**Sinal de detecção.** Arquivo de rota que importa o model ou o ORM e chama
persistência diretamente, sem camada intermediária. Buscar `import` de modelo
dentro de arquivo de rota.

**Por que importa.** O fluxo da requisição fica preso à definição de rota. Não
há ponto único para validação e montagem de resposta.

**Severidade.** HIGH.

**Transformação.** T4, T5.

**Exemplo observado.**

```python
from models.task import Task

@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    db.session.delete(task)
    db.session.commit()
```

### H3 — Estado global mutável

**Sinal de detecção.** Variável de módulo reatribuída por função; uso de
`global`; objeto exportado e mutado por outro módulo; acumulador que cresce sem
limite ou política de expiração.

**Por que importa.** O comportamento depende da ordem de execução. Um acumulador
sem limite cresce enquanto o processo viver.

**Severidade.** HIGH. CRITICAL quando o estado é compartilhado por toda a
aplicação e determina o acesso a dados.

**Transformação.** T6.

**Exemplo observado.**

```javascript
let globalCache = {};

function logAndCache(key, data) {
    globalCache[key] = data;      // sem limite, sem expiração
}
```

```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```

### H4 — Acoplamento direto a implementação concreta

**Sinal de detecção.** Instanciação de driver de banco, cliente HTTP, ou cliente
de e-mail dentro de construtor ou de função de regra. Importação de módulo de
infraestrutura dentro da camada de modelo.

**Por que importa.** A origem dos dados não pode ser trocada nem substituída
sem editar a regra.

**Severidade.** HIGH. Ver DIP em `solid-principles.md`.

**Transformação.** T6.

**Exemplo observado.**

```javascript
constructor() {
    this.db = new sqlite3.Database(':memory:');
}
```

### H5 — Aninhamento de callbacks com fluxo de erro divergente

**Sinal de detecção.** Três ou mais níveis de callback; retorno de resposta
dentro de callback interno; mistura de `function()` e arrow function para
recuperar `this`; variável de apoio como `self` ou `that`.

**Por que importa.** Cada nível tem tratamento de erro próprio e o fluxo de
sucesso fica espalhado. Um erro em nível interno pode deixar a requisição sem
resposta ou produzir duas respostas.

**Severidade.** HIGH.

**Transformação.** T8.

**Exemplo observado.**

```javascript
const self = this;
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        this.db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
            self.db.run("INSERT INTO payments ...", [...], function (err) {
                self.db.run("INSERT INTO audit_logs ...", [...], (err) => {
                    res.status(200).json({ msg: "Sucesso" });
                });
            });
        });
    });
});
```

### H6 — Escrita em múltiplos passos sem transação

**Sinal de detecção.** Duas ou mais operações de escrita relacionadas sem bloco
transacional; ausência de `rollback` no caminho de erro; `commit` único ao final
de um laço de escrita.

**Por que importa.** Falha no meio da sequência deixa o banco em estado
parcial: pedido sem itens, matrícula sem pagamento, estoque debitado sem pedido.

**Severidade.** HIGH.

**Transformação.** T9.

**Exemplo observado.**

```python
cursor.execute("INSERT INTO pedidos ...")
pedido_id = cursor.lastrowid
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()      # falha em qualquer ponto acima deixa estado parcial
```

### H7 — Exceção capturada e descartada

**Sinal de detecção.** `except:` sem tipo; `except Exception:` sem registro nem
reemissão; `catch (e) {}` vazio; `try` cujo bloco de tratamento devolve mensagem
genérica sem registrar a causa.

**Por que importa.** A causa raiz desaparece. O diagnóstico em produção fica
limitado ao código de status.

**Severidade.** HIGH.

**Transformação.** T11.

**Exemplo observado.**

```python
    except:
        return jsonify({'error': 'Erro interno'}), 500
```

### H8 — Política de origem cruzada aberta

**Sinal de detecção.** `CORS(app)` sem argumento de origem;
`Access-Control-Allow-Origin: *`; `cors()` sem opções.

**Por que importa.** Qualquer origem passa a poder emitir requisições
autenticadas pelo navegador contra a API.

**Severidade.** HIGH.

**Transformação.** T19. Aplicada com o padrão aberto, fecha como `MITIGADA`,
não como `CORRIGIDA`. Adotar lista restritiva como padrão é grupo 3.

**Exemplo observado.**

```python
CORS(app)
```

---

## MEDIUM

### M1 — Consulta dentro de laço

**Sinal de detecção.** Chamada de `execute`, `query`, `get`, `all`, ou `find`
dentro de `for`, `while`, `forEach`, ou `map`. Sinal auxiliar: criação de mais
de um cursor dentro do mesmo laço.

**Por que importa.** O número de idas ao banco cresce com o número de
registros. Um relatório com N pedidos e M itens executa 1 + N + N×M consultas.

**Severidade.** MEDIUM.

**Transformação.** T7.

**Exemplo observado.**

```python
for row in rows:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

### M2 — Lógica duplicada

**Sinal de detecção.** Mesmo bloco condicional ou mesmo dicionário de campos
repetido em dois ou mais pontos. Sinal auxiliar de alta confiança: existe um
método na entidade que implementa exatamente a lógica repetida e não é chamado
em nenhum lugar.

**Por que importa.** A correção precisa ser aplicada em todos os pontos. Um
ponto esquecido produz comportamento divergente entre endpoints.

**Severidade.** MEDIUM.

**Transformação.** T10.

**Exemplo observado.** O mesmo cálculo de atraso aparece nos handlers de
listagem, detalhe, estatística, listagem por usuário e relatório, enquanto a
entidade define:

```python
class Task(db.Model):
    def is_overdue(self):
        if self.due_date:
            if self.due_date < datetime.utcnow():
                if self.status != 'done' and self.status != 'cancelled':
                    return True
        return False
```

### M3 — Validação de entrada ausente ou incompleta

**Sinal de detecção.** Campo lido da requisição e persistido sem verificação de
tipo, faixa ou formato. Sinal auxiliar: existe função de validação no projeto
que não é chamada no caminho de escrita.

**Por que importa.** Dado inválido chega ao banco e falha depois, em um ponto
distante da origem.

**Severidade.** MEDIUM.

**Transformação.** T20. Grupo 3, altera o contrato, quando a validação nova
passa a recusar entrada hoje aceita e persistida; essa decisão é tomada na
Fase 2, nunca na Fase 3.

**Exemplo observado.**

```python
category.color = data.get('color', '#000000')     # aceita qualquer string
```

com a verificação disponível e não usada:

```python
def is_valid_color(color):
    if color and len(color) == 7 and color[0] == '#':
        return True
    return False
```

### M4 — Tratamento de erro não centralizado

**Sinal de detecção.** Bloco `try` repetido em cada handler; formatos de erro
divergentes entre handlers; ausência de tratador registrado no ponto de entrada.

**Por que importa.** O formato do erro depende de qual handler falhou, e o
tratamento precisa ser replicado em cada novo endpoint.

**Severidade.** MEDIUM.

**Transformação.** T11.

**Exemplo observado.** Um projeto com quatorze handlers, cada um encerrando com:

```python
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

### M5 — Código morto e importação não utilizada

**Sinal de detecção.** Símbolo importado e não referenciado no arquivo; função,
classe, constante ou módulo definido e não referenciado em nenhum arquivo do
projeto.

**Por que importa.** Aumenta a superfície de leitura e sugere dependências que
não existem. Um módulo de serviço não usado pode ser lido como funcionalidade
ativa.

**Severidade.** MEDIUM.

**Transformação.** T12.

**Exemplo observado.**

```python
import os, sys, json, datetime      # apenas datetime é usado
```

```javascript
const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');
// totalRevenue não é referenciado
```

```python
from utils.helpers import format_date, calculate_percentage
# nenhuma das duas é chamada no arquivo
```

### M6 — Uso de API obsoleta

**Sinal de detecção.** Ver `deprecated-apis.md`. Resolver cada símbolo contra a
versão declarada da dependência.

**Por que importa.** A remoção em versão futura quebra o projeto, e o
comportamento atual pode divergir do substituto.

**Severidade.** MEDIUM.

**Transformação.** T14.

**Exemplo observado.**

```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
task = Task.query.get(task_id)
```

---

## LOW

### L1 — Número mágico

**Sinal de detecção.** Literal numérico ou de texto com significado de negócio
usado diretamente em comparação ou cálculo, sem nome.

**Por que importa.** O significado do valor não é recuperável pela leitura, e a
alteração exige localizar todas as ocorrências.

**Severidade.** LOW.

**Transformação.** T13.

**Exemplo observado.**

```python
if faturamento > 10000:
    desconto = faturamento * 0.1
```

```python
if len(title) < 3: ...
if len(title) > 200: ...
```

### L2 — Nome sem significado

**Sinal de detecção.** Identificador de um ou dois caracteres fora de índice de
laço; abreviação não convencional; nome que sombreia identificador embutido da
linguagem.

**Por que importa.** Obriga a reconstruir o significado a cada leitura.

**Severidade.** LOW.

**Transformação.** T21.

**Exemplo observado.**

```javascript
let u = req.body.usr;
let e = req.body.eml;
let p = req.body.pwd;
let cid = req.body.c_id;
let cc = req.body.card;
```

```python
def buscar_produto(id):      # sombreia o built-in id
```

### L3 — Saída em terminal como registro de log

**Sinal de detecção.** `print(`, `console.log(` fora de script de linha de
comando, sem nível, sem destino configurável.

**Por que importa.** Não há como filtrar por severidade nem direcionar para
coletor. Dado sensível impresso não pode ser suprimido por configuração.

**Severidade.** LOW. Sobe para CRITICAL quando o conteúdo impresso é dado
sensível, e nesse caso a constatação é C6.

**Transformação.** T23.

**Exemplo observado.**

```python
print("Login bem-sucedido: " + email)
```

```javascript
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

O segundo exemplo registra número de cartão e chave de gateway, portanto é
reportado como C6, não como L3.

### L4 — Formato de resposta inconsistente

**Sinal de detecção.** Endpoints do mesmo projeto devolvendo envelopes
diferentes: array puro em um, objeto com envelope em outro; chave de erro com
nomes diferentes entre handlers.

**Por que importa.** O cliente precisa de tratamento por endpoint em vez de
tratamento único.

**Severidade.** LOW.

**Transformação.** T22. Grupo 3, altera o contrato, quando a padronização
muda o corpo de respostas existentes.

**Exemplo observado.**

```python
return jsonify(result), 200                       # lista: array puro
return jsonify({'error': 'Task não encontrada'}), 404   # erro: objeto
```

### L5 — Literal de domínio repetido

**Sinal de detecção.** Mesma lista de valores válidos, mesmo conjunto de status
ou papéis, escrito em dois ou mais arquivos.

**Por que importa.** Acrescentar um valor exige localizar todas as cópias.
Cópias divergentes produzem validação inconsistente entre endpoints.

**Severidade.** LOW.

**Transformação.** T13.

**Exemplo observado.** A mesma lista aparece na entidade, em dois handlers e no
módulo de apoio:

```python
valid = ['pending', 'in_progress', 'done', 'cancelled']
if status not in ['pending', 'in_progress', 'done', 'cancelled']:
VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
```

---

## Índice rápido de sinais

| Buscar por | Entradas candidatas |
|---|---|
| `execute(` com `+`, `f"`, `%`, `.format(`, `${` | C1 |
| `secret`, `key`, `token`, `password`, `pwd` em atribuição literal | C2 |
| `eval`, `exec`, `system`, `execute(` de corpo da requisição | C3 |
| `DELETE FROM`, `DROP`, `TRUNCATE` em handler | C4 |
| `md5`, `sha1`, `base64`, comparação direta de senha | C5 |
| `password`, `secret_key` em objeto de resposta | C6 |
| arquivo com esquema, rota e regra juntos | C7 |
| `debug=True`, `DEBUG = True` | C8 |
| cálculo ou agregação dentro de handler | H1 |
| `import` de modelo dentro de arquivo de rota | H2 |
| `global`, variável de módulo reatribuída | H3 |
| `new` de driver dentro de construtor | H4 |
| três ou mais níveis de callback, `const self = this` | H5 |
| dois `INSERT` ou `UPDATE` sem bloco transacional | H6 |
| `except:`, `catch (e) {}` | H7 |
| `CORS(app)` sem origem | H8 |
| `execute`, `query`, `get` dentro de laço | M1 |
| bloco condicional repetido, método de entidade não chamado | M2 |
| campo persistido sem verificação | M3 |
| `try` em cada handler | M4 |
| símbolo importado e não referenciado | M5 |
| símbolos de `deprecated-apis.md` | M6 |
| literal numérico em comparação de negócio | L1 |
| identificador de um caractere fora de laço | L2 |
| `print(`, `console.log(` | L3 |
| envelopes de resposta divergentes | L4 |
| mesma lista de valores em dois arquivos | L5 |
