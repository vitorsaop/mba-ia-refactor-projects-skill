# Arquitetura alvo: Model-View-Controller

## Conteúdo

- O que é MVC
- As três camadas e as duas camadas de apoio
- Tabela contém / não contém
- Fluxo de uma requisição
- Regra de dependência
- Exemplo completo em Python/Flask
- Exemplo completo em Node.js/Express
- Absorção de diretórios que o MVC não nomeia
- Convenção de diretórios por stack
- Preservação do ponto de entrada
- Preservação de comportamento
- Como auditar violação de camada

## O que é MVC

Model-View-Controller separa uma aplicação em três responsabilidades que mudam
por motivos diferentes.

- **Model** muda quando a regra de negócio ou o formato dos dados muda.
- **View** muda quando a forma de apresentar ou expor os dados muda.
- **Controller** muda quando o fluxo entre entrada e saída muda.

Em uma API HTTP sem interface gráfica, a View é a camada de roteamento e
serialização: o que define quais caminhos existem e em que formato a resposta
sai. Não existe template renderizado, e isso não elimina a camada; apenas muda o
que ela produz.

O objetivo prático da separação é que uma mudança de regra de negócio não exija
tocar em roteamento, e uma mudança de rota não exija tocar em SQL.

## As três camadas e as duas camadas de apoio

### Model

Responsável por dados e regra de negócio.

- Acesso ao banco, sempre com consulta parametrizada.
- Invariantes da entidade: o que torna um registro válido.
- Cálculos de domínio: totais, descontos, prazos, contagens.
- Conversão da entidade para estrutura de dados simples.

### View, ou Routes

Responsável por expor a aplicação.

- Associação entre caminho, método HTTP e controller.
- Prefixos e agrupamentos de rota.
- Nada além disso.

### Controller

Responsável por orquestrar uma requisição.

- Ler entrada da requisição.
- Validar formato da entrada.
- Chamar o model.
- Traduzir o retorno do model em corpo de resposta e código de status.

### Config, camada de apoio

- Leitura de variáveis de ambiente.
- Constantes nomeadas que hoje aparecem como número ou literal solto.
- Nenhum valor secreto embutido no código.

### Middlewares, camada de apoio

- Tratamento de erro centralizado.
- Registro de log.
- Política de origem cruzada.
- Autenticação, quando existir.

## Tabela contém / não contém

Esta tabela é o critério objetivo da auditoria de camada.

| Camada | Contém | Não contém |
|---|---|---|
| `config/` | leitura de ambiente, constantes nomeadas | consulta, rota, regra de negócio |
| `models/` | acesso a dados, consulta parametrizada, invariantes, cálculo de domínio | objeto de requisição, objeto de resposta, código de status HTTP, definição de rota |
| `controllers/` | leitura de entrada, validação de formato, chamada ao model, montagem da resposta | SQL literal, acesso direto ao driver do banco, definição de rota |
| `views/` ou `routes/` | associação caminho, método e controller | regra de negócio, acesso a dados, validação de campo |
| `middlewares/` | tratamento de erro, log, origem cruzada, autenticação | regra de domínio, consulta de entidade |
| ponto de entrada | composição das camadas, inicialização | qualquer uma das responsabilidades acima |
| `services/` ou `application/` (descritiva) | orquestração de vários models, transação de caso de uso | objeto de requisição, objeto de resposta, definição de rota |
| `utils/` ou `helpers/` (descritiva) | função pura, sem estado e sem literal de domínio | regra de negócio, validação de campo, configuração, estado de módulo |

As duas últimas linhas são **descritivas**, não prescritivas: elas descrevem
tipos de diretório que projetos reais trazem e como julgá-los. A estrutura alvo
continua sendo as cinco camadas mais o ponto de entrada, conforme a tabela de
convenção.

## Fluxo de uma requisição

```
requisição HTTP
      |
      v
[ view / route ]     resolve caminho e método, chama o controller
      |
      v
[ controller ]       lê entrada, valida formato, chama o model
      |
      v
[ model ]            aplica regra, acessa dados, devolve estrutura simples
      |
      v
[ controller ]       monta corpo e código de status
      |
      v
[ middleware ]       intercepta erro não tratado
      |
      v
resposta HTTP
```

## Regra de dependência

As setas de importação apontam sempre para dentro.

```
routes  ->  controllers  ->  models  ->  config
```

- `routes` importa `controllers`.
- `controllers` importa `models`.
- `models` importa `config`.
- Nenhuma seta na direção contrária. Um `model` que importa `controllers` é
  violação de camada.
- `middlewares` é importado apenas pelo ponto de entrada.

## Exemplo completo em Python/Flask

O exemplo percorre um mesmo endpoint pelas quatro camadas.

### Antes: uma função com todas as responsabilidades

```python
# app.py
@app.route("/produtos/<int:id>", methods=["GET"])
def buscar_produto(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
    row = cursor.fetchone()
    if row is None:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": {
        "id": row["id"], "nome": row["nome"], "preco": row["preco"],
    }, "sucesso": True}), 200
```

Problemas verificáveis: roteamento, SQL, serialização e código de status no
mesmo bloco; consulta montada por concatenação.

### Depois: quatro arquivos

```python
# src/config/settings.py
import os
import secrets

# Valor não secreto: o literal atual vira o padrão. Os padrões abaixo são os
# valores que estavam embutidos no código de boot deste projeto.
DB_PATH = os.getenv("DB_PATH", "loja.db")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

# Segredo: nenhum literal no código. Gerado por boot quando ausente.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
```

Valor não secreto mantém o literal atual como padrão, então o boot continua
funcionando sem arquivo de ambiente e o comportamento em execução não muda.
Segredo não mantém literal algum: manter o segredo como valor padrão apenas o
muda de arquivo e não resolve o problema. A classificação completa dos valores
está em T2, em `refactoring-playbook.md`.

```python
# src/models/produto_model.py
from src.config.database import get_connection

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria",
          "ativo", "criado_em")


def _to_dict(row):
    return {campo: row[campo] for campo in CAMPOS}


def get_by_id(produto_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
    return _to_dict(row) if row else None
```

O model devolve `None`, não uma resposta HTTP. Ele não sabe que existe HTTP.

```python
# src/controllers/produto_controller.py
from flask import jsonify
from src.models import produto_model


def buscar_produto(id):
    produto = produto_model.get_by_id(id)
    if produto is None:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200
```

O controller traduz `None` em 404 e dicionário em 200. As chaves `erro`,
`sucesso` e `dados` são idênticas às originais.

```python
# src/views/routes.py
from flask import Blueprint
from src.controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)

produto_bp.add_url_rule(
    "/produtos/<int:id>", "buscar_produto",
    produto_controller.buscar_produto, methods=["GET"],
)
```

```python
# src/middlewares/error_handler.py
from flask import jsonify
from werkzeug.exceptions import HTTPException


def register(app):
    @app.errorhandler(Exception)
    def handle(exc):
        if isinstance(exc, HTTPException):
            return exc          # preserva 404 de rota inexistente, 405 e demais
        app.logger.exception("erro não tratado")
        return jsonify({"erro": str(exc)}), 500
```

O tratador central substitui o `try/except` repetido em cada controller e
mantém o mesmo corpo de resposta que aqueles blocos produziam. A guarda
`isinstance(exc, HTTPException)` é obrigatória: sem ela o tratador captura
também as exceções de HTTP do roteamento e converte 404 e 405 em 500. Ver T11 em
`refactoring-playbook.md`.

```python
# app.py  (raiz, nome preservado)
from src.app import create_app
from src.config import settings

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

```python
# src/app.py  (composition root)
from flask import Flask
from flask_cors import CORS
from src.config import settings
from src.views.routes import produto_bp
from src.middlewares import error_handler


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app)
    app.register_blueprint(produto_bp)
    error_handler.register(app)
    return app
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

O `app.py` da raiz continua existindo com o mesmo nome, então `python app.py`
segue funcionando. Um `seed.py` que faz `from app import app, db` também
continua funcionando, porque os símbolos permanecem exportados.

## Exemplo completo em Node.js/Express

### Antes: classe com esquema, rota, pagamento e persistência

```javascript
// src/AppManager.js
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }

    setupRoutes(app) {
        app.post('/api/checkout', (req, res) => {
            let cid = req.body.c_id;
            let cc = req.body.card;
            this.db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid], (err, course) => {
                if (err || !course) return res.status(404).send("Curso não encontrado");
                let status = cc.startsWith("4") ? "PAID" : "DENIED";
                if (status === "DENIED") return res.status(400).send("Pagamento recusado");
                // ... mais três níveis de callback aninhado
            });
        });
    }
}
```

### Depois

```javascript
// src/config/settings.js
const require_ = (nome) => {
    const valor = process.env[nome];
    if (!valor) {
        throw new Error(
            `variavel de ambiente ${nome} nao definida. ` +
            `Copiar .env.example para .env e preencher.`
        );
    }
    return valor;
};

module.exports = {
    // Valores não secretos: o literal atual vira o padrão.
    port: Number(process.env.PORT || 3000),
    dbFile: process.env.DB_FILE || ':memory:',
    // Segredo: sem literal e sem padrão. Só é exigido quando usado.
    paymentGatewayKey: () => require_('PAYMENT_GATEWAY_KEY'),
};
```

O segredo é exposto como função, não como valor, para que a ausência da variável
falhe no momento do uso e não no carregamento do módulo. Assim a aplicação sobe
e os endpoints que não dependem do gateway continuam respondendo.

```javascript
// src/models/courseModel.js
class CourseModel {
    constructor(db) { this.db = db; }

    findActiveById(id) {
        return this.db.get(
            'SELECT * FROM courses WHERE id = ? AND active = 1', [id]
        );
    }
}
module.exports = CourseModel;
```

O model recebe `db` pelo construtor em vez de instanciar o driver. Isso remove o
acoplamento ao SQLite e permite trocar a fonte de dados sem tocar no model.

```javascript
// src/models/paymentModel.js
const APPROVED_CARD_PREFIX = '4';

class PaymentModel {
    constructor(db) { this.db = db; }

    // Regra de negócio preservada: cartão iniciado em 4 é aprovado.
    authorize(cardNumber) {
        return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? 'PAID' : 'DENIED';
    }

    async record(enrollmentId, amount, status) {
        const result = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return result.lastID;
    }
}
module.exports = PaymentModel;
```

O prefixo vira constante nomeada, mas o valor `'4'` e o resultado da regra
permanecem idênticos.

```javascript
// src/controllers/checkoutController.js
class CheckoutController {
    constructor({ courseModel, userModel, enrollmentModel, paymentModel }) {
        Object.assign(this, { courseModel, userModel, enrollmentModel, paymentModel });
    }

    handle = async (req, res, next) => {
        try {
            const { usr, eml, pwd, c_id: courseId, card } = req.body;
            if (!usr || !eml || !courseId || !card) {
                return res.status(400).send('Bad Request');
            }

            const course = await this.courseModel.findActiveById(courseId);
            if (!course) return res.status(404).send('Curso não encontrado');

            const status = this.paymentModel.authorize(card);
            if (status === 'DENIED') return res.status(400).send('Pagamento recusado');

            const userId = await this.userModel.findOrCreateByEmail(eml, usr, pwd);
            const enrollmentId = await this.enrollmentModel.create(userId, courseId);
            await this.paymentModel.record(enrollmentId, course.price, status);

            return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (err) {
            return next(err);
        }
    };
}
module.exports = CheckoutController;
```

Os quatro níveis de callback viram sequência linear. Os códigos 400, 404 e 200 e
as chaves `msg` e `enrollment_id` são os mesmos.

```javascript
// src/routes/index.js
const { Router } = require('express');

module.exports = ({ checkoutController, reportController, userController }) => {
    const router = Router();
    router.post('/api/checkout', checkoutController.handle);
    router.get('/api/admin/financial-report', reportController.financial);
    router.delete('/api/users/:id', userController.remove);
    return router;
};
```

```javascript
// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
    console.error(err);
    res.status(500).send('Erro interno');
};
```

```javascript
// src/app.js  (entry point preservado, alvo de npm start)
const express = require('express');
const settings = require('./config/settings');
const buildContainer = require('./container');
const buildRoutes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());

const container = buildContainer(settings);
container.initDb();
app.use(buildRoutes(container));
app.use(errorHandler);

app.listen(settings.port, () => {
    console.log(`Servidor na porta ${settings.port}`);
});
```

`package.json` aponta `start` para `node src/app.js`. O caminho não muda, então
`npm start` continua funcionando.

## Absorção de diretórios que o MVC não nomeia

Diretório pré-existente que não é uma das cinco camadas **não é apagado nem
preservado por padrão**. Cada arquivo dele é classificado pelo conteúdo, contra
a tabela acima, e movido para a camada a que o conteúdo pertence.

**Teste de resíduo.** Um arquivo só permanece fora das cinco camadas quando as
três condições valem ao mesmo tempo:

1. toda função nele é totalmente determinada pelos argumentos;
2. o arquivo não contém literal do tipo que o Grupo 1 declara invariante: faixa
   numérica, limite, prefixo de decisão, lista de valores válidos;
3. o arquivo não tem estado mutável de módulo.

Falhando qualquer uma, o arquivo é classificado e movido, e a classificação
entra na tabela `origem -> destino` do plano.

| Conteúdo | Destino |
|---|---|
| formatação de data, cálculo de porcentagem | permanece: é função pura sem literal de domínio |
| validação contra lista de status ou faixa de tamanho | `controllers/`: é validação de entrada |
| objeto de configuração | `config/` |
| cache ou contador de módulo | não é resíduo: é constatação de estado global, H3 |

## Convenção de diretórios por stack

| Camada | Python/Flask | Node.js/Express |
|---|---|---|
| Configuração | `src/config/settings.py` | `src/config/settings.js` |
| Modelos | `src/models/<dominio>_model.py` | `src/models/<Dominio>Model.js` |
| Controladores | `src/controllers/<dominio>_controller.py` | `src/controllers/<dominio>Controller.js` |
| Rotas | `src/views/routes.py` | `src/routes/index.js` |
| Middlewares | `src/middlewares/error_handler.py` | `src/middlewares/errorHandler.js` |
| Composition root | `src/app.py` | `src/app.js` |
| Entrada preservada | `app.py` na raiz | `src/app.js` |

Para outra stack, manter os mesmos cinco diretórios e adotar a convenção de
nomenclatura da linguagem. A estrutura de camadas não muda; apenas o nome dos
arquivos.

Usar sempre barra normal nos caminhos, inclusive em Windows.

## Preservação do ponto de entrada

Antes de mover qualquer arquivo, localizar o comando de boot documentado:

1. seção de execução do `README.md` do projeto;
2. campo `scripts.start` do `package.json`;
3. campo `main` do `package.json`;
4. bloco `if __name__ == "__main__":`.

O arquivo apontado por esse comando mantém caminho e nome. Se o código dele for
movido para `src/`, o arquivo original vira um carregador de duas ou três
linhas.

Verificar também quais símbolos outros scripts do projeto importam do ponto de
entrada. Um `seed.py` com `from app import app, db` exige que `app` e `db`
continuem exportados pelo `app.py` da raiz.

**O contrato não para no ponto de entrada.** Antes de mover qualquer arquivo,
enumerar todo script executável do projeto:

- o que a sequência de execução do README nomeia;
- o que os campos de script do manifesto nomeiam;
- o que carrega o marcador de entrada executável da linguagem:
  `if __name__ == "__main__":` em Python, `require.main === module` em Node,
  `func main()` em Go.

Para cada um, registrar **todo caminho de módulo que ele importa**, não apenas
os símbolos vindos do ponto de entrada. Esses caminhos fazem parte do contrato
preservado. Para cada caminho, uma de três coisas: o caminho sobrevive; existe
um repassador no caminho antigo reexportando os símbolos movidos; ou o script é
atualizado na mesma transformação. Qualquer repassador aparece na tabela
`origem -> destino` do plano.

O caso concreto: um `seed.py` que faz `from models.task import Task` além de
`from app import app, db` quebra quando `models/` passa a viver sob `src/`. O
boot da aplicação não exercita esse import, e a captura também não. O passo 6 do
Passo 3 de `validation-protocol.md` é o único lugar onde isso aparece.

## Preservação de comportamento

As mudanças são classificadas em três grupos.

### Grupo 1: invariante

Nunca alterado.

- Caminho da rota, método HTTP e código de status de sucesso.
- Chaves do corpo de resposta e o significado de cada valor.
- Fórmulas de cálculo, faixas numéricas, prefixos de decisão e listas de valores
  válidos.

### Grupo 2: corrigido por padrão

Altera a implementação, não a saída para entrada legítima.

- Consulta concatenada para consulta parametrizada.
- Segredo embutido para variável de ambiente com o literal atual como padrão.
- Conexão global única para conexão com escopo de aplicação.
- Consulta dentro de laço para consulta única.
- Lógica duplicada para função única.
- `print` para registro de log com nível.
- Remoção de dado sensível do log.
- Remoção de código morto e de importação não utilizada.
- API obsoleta para o substituto oficial.

### Grupo 3: altera o contrato

Exige autorização no portão da Fase 2. Aplica-se quando a correção:

- remove um endpoint;
- remove ou renomeia chave do corpo de resposta;
- altera o texto de uma resposta;
- invalida dado já persistido, como troca de algoritmo de senha;
- altera o estado do banco resultante de uma operação;
- passa a recusar entrada hoje aceita e persistida.

Constatação do grupo 3 recebe a marca `[contract-breaking]` no relatório e o campo
`Contract change:`. Ela mantém a própria severidade: o grupo descreve o
efeito da correção, não a gravidade do problema, e uma constatação MEDIUM pode
alterar o contrato tanto quanto uma CRITICAL. Se não for autorizada, aparece em
`## Não aplicadas` no bloco da Fase 3.

**A classificação de grupo é decidida na Fase 2.** Descobrir na Fase 3 que uma
correção pertence ao grupo 3 é reclassificação, e reclassificação volta ao
usuário por um portão estreito. Descartar a correção com base na própria
reclassificação é o caminho pelo qual uma constatação desaparece sem que
ninguém decida. Ver `remediation-protocol.md`, "Reclassificação depois do
portão".

### Quando a correção do grupo 2 preserva a condição insegura

Algumas transformações do grupo 2 prescrevem manter o valor atual como padrão,
justamente para preservar o comportamento. Quando esse valor é a condição
insegura descrita na constatação, a correção muda a estrutura e não encerra o
achado.

Esse resultado é registrado como `MITIGADA`, não como `CORRIGIDA`, e o residual
aparece em `## Risco residual`. Tratá-lo como corrigido faz o achado sair do
relatório sem ter saído do código.

## Como auditar violação de camada

Para cada arquivo do projeto:

1. Determinar a qual camada o arquivo pertence, pelo diretório e pelo conteúdo.
2. Aplicar a coluna `não contém` da tabela.
3. Cada item encontrado é uma constatação, com o intervalo de linhas exato.

Mapeamento de severidade:

| Violação | Severidade |
|---|---|
| Um arquivo concentra dados, regra, roteamento e configuração | CRITICAL |
| Regra de negócio dentro de rota ou controller | HIGH |
| Camada de controller inexistente, rota chamando o model direto | HIGH |
| Model devolvendo objeto de resposta HTTP | HIGH |
| Rota executando validação de campo | MEDIUM |
| Ponto de entrada com regra além da composição | MEDIUM |
| Regra de domínio ou validação de entrada em módulo fora das cinco camadas | MEDIUM |
