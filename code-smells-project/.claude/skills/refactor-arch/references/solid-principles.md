# Princípios SOLID: definição, detecção e transformação

## Conteúdo

- Como usar este arquivo
- SRP, responsabilidade única
- OCP, aberto para extensão e fechado para modificação
- LSP, substituição de Liskov
- ISP, segregação de interface
- DIP, inversão de dependência
- Tabela de severidade
- Relação entre SOLID e MVC

## Como usar este arquivo

A escala de severidade do relatório é definida em termos de MVC e SOLID. Este
arquivo fornece, para cada princípio: a definição, o sinal de detecção
buscável no código, a severidade correspondente e um par antes/depois.

Regras de aplicação:

1. Uma constatação de SOLID exige o mesmo rigor das demais: arquivo e intervalo
   de linhas confirmados por leitura.
2. Um mesmo trecho pode violar mais de um princípio. Reportar a violação de
   maior severidade e citar as demais no campo `Description`.
3. Não reportar violação de princípio sem apontar o trecho concreto. Frase
   genérica sobre acoplamento não é constatação.

## SRP, responsabilidade única

**Definição.** Um módulo deve ter uma, e apenas uma, razão para mudar. Duas
responsabilidades no mesmo módulo significam que uma mudança em qualquer das
duas obriga a tocar no mesmo arquivo.

**Sinais de detecção.**

- Um arquivo contém, ao mesmo tempo: criação de esquema, consulta, regra de
  negócio, roteamento e formatação de saída.
- Um arquivo cobre mais de um domínio de negócio.
- Uma função executa validação, persistência e notificação.
- Um arquivo com mais de 250 linhas cujos nomes de função pertencem a
  substantivos diferentes.

**Severidade.** CRITICAL quando um único arquivo concentra dados, regra e
roteamento. HIGH quando concentra dois desses três.

### Antes

```python
# models.py - um módulo, quatro domínios, três responsabilidades
def get_todos_produtos(): ...        # domínio produto,  acesso a dados
def criar_produto(...): ...          # domínio produto,  acesso a dados
def get_todos_usuarios(): ...        # domínio usuário,  acesso a dados
def login_usuario(email, senha): ... # domínio usuário,  autenticação
def criar_pedido(usuario_id, itens): # domínio pedido,   regra de negócio
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
        produto = cursor.fetchone()
        if produto["estoque"] < item["quantidade"]:
            return {"erro": "Estoque insuficiente para " + produto["nome"]}
        total = total + (produto["preco"] * item["quantidade"])
def relatorio_vendas(): ...          # domínio relatório, cálculo e agregação
```

Razões para mudar este arquivo: mudança no catálogo de produtos, no cadastro de
usuários, na regra de estoque, na política de desconto e no esquema do banco.
Cinco razões, um arquivo.

### Depois

```
src/models/
├── produto_model.py     # razão para mudar: catálogo de produtos
├── usuario_model.py     # razão para mudar: cadastro e autenticação
├── pedido_model.py      # razão para mudar: regra de pedido e estoque
└── relatorio_model.py   # razão para mudar: política de relatório
```

```python
# src/models/pedido_model.py
from src.models import produto_model


def calcular_total(itens):
    total = 0
    for item in itens:
        produto = produto_model.get_by_id(item["produto_id"])
        if produto is None:
            raise ProdutoInexistente(item["produto_id"])
        if produto["estoque"] < item["quantidade"]:
            raise EstoqueInsuficiente(produto["nome"])
        total += produto["preco"] * item["quantidade"]
    return total
```

O módulo de pedido passou a ter uma razão para mudar: a regra de pedido. A
consulta de produto ficou no módulo de produto.

## OCP, aberto para extensão e fechado para modificação

**Definição.** Deve ser possível acrescentar comportamento sem editar o código
existente. Uma cadeia condicional que cresce a cada novo caso é o sinal oposto.

**Sinais de detecção.**

- Cadeia `if / elif / else` sobre um valor de domínio, com um ramo por caso.
- `switch` sobre tipo ou status com um ramo por valor.
- Lista de valores válidos escrita em mais de um arquivo.
- Cada novo caso de negócio exige editar uma função existente.

**Severidade.** MEDIUM. Sobe para HIGH quando a mesma cadeia está duplicada em
mais de um arquivo, porque a extensão exige edições sincronizadas.

### Antes

```python
# models.py - faixa de desconto por cadeia condicional
desconto = 0
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
elif faturamento > 1000:
    desconto = faturamento * 0.02
```

Acrescentar uma faixa exige editar esta função e reordenar as comparações.

### Depois

```python
# src/config/settings.py
# Faixas ordenadas do maior limite para o menor.
# Valores idênticos aos da implementação original.
FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000,  0.05),
    (1000,  0.02),
)
```

```python
# src/models/relatorio_model.py
from src.config.settings import FAIXAS_DESCONTO


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0
```

Acrescentar uma faixa passa a ser acrescentar uma tupla à configuração. A função
não muda. Para os mesmos valores de entrada, o resultado é idêntico ao anterior.

## LSP, substituição de Liskov

**Definição.** Um subtipo deve poder substituir o tipo base sem que o código
que usa o tipo base deixe de funcionar. O subtipo não pode exigir mais entrada
nem entregar menos garantia do que o tipo base.

**Sinais de detecção.**

- Método sobrescrito que lança exceção onde o método base retorna valor.
- Subclasse que rejeita entrada aceita pela superclasse.
- Código que testa o tipo concreto antes de chamar um método, com `isinstance`,
  `instanceof` ou comparação de nome de classe.
- Método sobrescrito que devolve tipo diferente do declarado na base.

**Severidade.** HIGH, porque quebra o contrato de quem consome a abstração.

**Ocorrência nos projetos de referência.** Nenhuma violação confirmada. Os três
projetos não possuem hierarquia de herança com sobrescrita de método: a única
herança presente é de classe base de ORM, sem redefinição de comportamento
herdado. Registrar este resultado no relatório como ausência de constatação, não
como constatação de severidade zero.

### Exemplo ilustrativo do sinal

Trecho sintético, apresentado apenas para fixar o padrão de detecção.

```python
class Repositorio:
    def salvar(self, registro):
        """Persiste e devolve o identificador."""
        ...
        return registro_id


class RepositorioSomenteLeitura(Repositorio):
    def salvar(self, registro):
        raise NotImplementedError("repositório somente leitura")
```

Quem recebe um `Repositorio` e chama `salvar` funciona com a base e falha com o
subtipo. A correção é separar a capacidade de escrita em uma abstração própria,
em vez de sobrescrever com falha.

```python
class RepositorioLeitura:
    def buscar(self, registro_id): ...


class RepositorioEscrita(RepositorioLeitura):
    def salvar(self, registro): ...
```

## ISP, segregação de interface

**Definição.** Nenhum consumidor deve ser obrigado a depender de partes que não
usa. Uma interface ampla força quem precisa de um método a carregar todos os
outros.

**Sinais de detecção.**

- Uma classe agrupa capacidades que consumidores diferentes usam em separado.
- Um consumidor precisa de uma função e importa um módulo com dezenas de
  símbolos não usados.
- Uma função de serialização única atende consumidores com necessidades
  diferentes, e o consumidor mais restritivo recebe campos a mais.
- Importação de símbolos que o arquivo não referencia.

**Severidade.** MEDIUM. Sobe para CRITICAL quando o excesso exposto é dado
sensível, porque nesse caso a violação de ISP é também vazamento de dado.

### Antes, caso de serialização única

```python
# models/user.py
class User(db.Model):
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password,   # hash exposto a todos os consumidores
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }
```

Quatro endpoints consomem `to_dict`. Nenhum deles precisa do campo de senha, e
todos o recebem.

### Depois

```python
# src/models/user_model.py
class User(db.Model):
    def to_public_dict(self):
        """Consumido por listagem, detalhe, criação e login."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def to_credential_dict(self):
        """Consumido apenas pela verificação de credencial."""
        return {'id': self.id, 'password': self.password}
```

Cada consumidor depende do conjunto mínimo. A remoção do campo `password` da
resposta altera o contrato, é do grupo 3, e depende de autorização no portão da
Fase 2.

### Antes, caso de serviço agrupado

```python
# services/notification_service.py
class NotificationService:
    def __init__(self):
        self.notifications = []
        self.email_host = 'smtp.gmail.com'
        self.email_port = 587
        self.email_user = 'taskmanager@gmail.com'
        self.email_password = 'senha123'

    def send_email(self, to, subject, body): ...       # transporte
    def notify_task_assigned(self, user, task): ...    # regra + transporte + registro
    def get_notifications(self, user_id): ...          # consulta do registro
```

Quem só precisa consultar notificações registradas carrega junto a configuração
de servidor de e-mail e a credencial.

### Depois

```python
# src/services/email_sender.py
class EmailSender:
    def __init__(self, host, port, user, password): ...
    def send(self, to, subject, body): ...
```

```python
# src/services/notification_store.py
class NotificationStore:
    def add(self, notification): ...
    def list_by_user(self, user_id): ...
```

```python
# src/services/notification_service.py
class NotificationService:
    def __init__(self, sender, store):
        self.sender = sender
        self.store = store

    def notify_task_assigned(self, user, task): ...
```

## DIP, inversão de dependência

**Definição.** Módulos de política não devem depender de módulos de detalhe.
Ambos devem depender de uma abstração. Em prática: o que decide não instancia o
que executa; recebe.

**Sinais de detecção.**

- `new` de driver de banco, cliente HTTP ou cliente de e-mail dentro de
  construtor ou de função de regra.
- Importação de módulo concreto de infraestrutura dentro da camada de modelo ou
  de controller.
- Estado global compartilhado obtido por função sem parâmetro.
- Impossibilidade de exercitar a função sem subir o banco.

**Severidade.** HIGH. Sobe para CRITICAL quando combinada com estado global
mutável compartilhado por toda a aplicação.

### Antes, Python

```python
# database.py
db_connection = None
db_path = "loja.db"


def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```

```python
# models.py
from database import get_db


def get_todos_produtos():
    db = get_db()          # a função busca sua própria dependência
    cursor = db.cursor()
    ...
```

Toda função do model depende de um singleton de módulo. Não há como trocar a
origem dos dados nem exercitar a função isoladamente.

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

```python
# src/models/produto_model.py
from src.config.database import get_connection


def get_all(connection_factory=get_connection):
    with connection_factory() as conn:
        rows = conn.execute("SELECT * FROM produtos").fetchall()
    return [_to_dict(row) for row in rows]
```

A origem da conexão passou a ser um parâmetro com valor padrão. O comportamento
em execução não muda, e a dependência deixou de ser fixa.

### Antes, Node.js

```javascript
class AppManager {
    constructor() {
        this.db = new sqlite3.Database(':memory:');   // política cria o detalhe
    }
}
```

### Depois, Node.js

```javascript
// src/container.js
const sqlite3 = require('sqlite3').verbose();
const CourseModel = require('./models/courseModel');
const PaymentModel = require('./models/paymentModel');

module.exports = (settings) => {
    const db = promisify(new sqlite3.Database(settings.dbFile));
    return {
        db,
        courseModel: new CourseModel(db),
        paymentModel: new PaymentModel(db),
    };
};
```

```javascript
// src/models/courseModel.js
class CourseModel {
    constructor(db) { this.db = db; }   // recebe a dependência
}
```

A instanciação concreta ficou concentrada no container, que é chamado apenas
pelo ponto de entrada. Nenhum model conhece o driver.

## Tabela de severidade

| Princípio | Condição | Severidade |
|---|---|---|
| SRP | um arquivo concentra dados, regra e roteamento | CRITICAL |
| SRP | um arquivo concentra duas dessas três responsabilidades | HIGH |
| SRP | um arquivo cobre mais de um domínio de negócio | HIGH |
| OCP | cadeia condicional por caso de domínio, em um arquivo | MEDIUM |
| OCP | mesma cadeia duplicada em mais de um arquivo | HIGH |
| LSP | subtipo que quebra o contrato do tipo base | HIGH |
| ISP | interface ampla forçada a consumidor restrito | MEDIUM |
| ISP | excesso exposto contém dado sensível | CRITICAL |
| ISP | importação de símbolo não utilizado | LOW |
| DIP | política instancia o detalhe de infraestrutura | HIGH |
| DIP | dependência via estado global mutável compartilhado | CRITICAL |

## Relação entre SOLID e MVC

MVC é a aplicação de SRP na dimensão das camadas. A regra de dependência de
`mvc-architecture.md`, com as setas apontando para dentro, é a aplicação de DIP
na mesma dimensão.

| Regra de MVC | Princípio correspondente |
|---|---|
| Cada camada tem uma responsabilidade | SRP |
| Model não conhece HTTP | SRP e DIP |
| Controller não contém SQL | SRP |
| Setas de importação apontam para dentro | DIP |
| Constantes e faixas em `config/` | OCP |
| Serialização específica por consumidor | ISP |

Uma constatação que viole simultaneamente uma regra de camada e um princípio é
reportada uma vez, com a maior severidade das duas.
