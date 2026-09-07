# refactor-arch: skill de auditoria e refatoração arquitetural

Skill que executa três fases sobre um projeto de backend: análise de stack,
auditoria contra catálogo de anti-patterns e refatoração para Model-View-Controller
com validação de comportamento por comparação de capturas HTTP.

Aplicada a três projetos de stacks diferentes. O enunciado original do desafio
está em [ENUNCIADO.md](ENUNCIADO.md).

| Projeto | Stack | Findings | Estrutura antes | Estrutura depois |
|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1 | 29 mais 15 da segunda execução | 4 arquivos, 780 linhas | 28 arquivos, 954 linhas |
| ecommerce-api-legacy | Node.js + Express 4.18.2 | 24 | 3 arquivos, 180 linhas | 22 arquivos, 969 linhas |
| task-manager-api | Python + Flask 3.0.0 | 53 mais 3 do adendo | 15 arquivos, 1158 linhas | 27 arquivos, 1614 linhas |

---

## A) Análise Manual

Três condições aparecem nos três projetos, com evidência distinta em cada um:
falta de organização, acoplamento e falta de coesão. As seções abaixo descrevem
onde cada uma se manifesta, com arquivo e contagem.

### Projeto 1: code-smells-project

Quatro arquivos na raiz, sem diretório de camada.

**Falta de organização.** `app.py` reunia configuração da aplicação, registro de
rotas e dois handlers que executavam SQL diretamente. `models.py` e
`controllers.py` tinham 314 e 292 linhas cobrindo os mesmos quatro domínios.
Não existiam os diretórios `config/`, `models/`, `controllers/`, `views/` e
`middlewares/`.

**Acoplamento.** `database.py` mantinha a conexão em variável de módulo
reatribuída por `get_db()`, com `check_same_thread` desativado, compartilhada
por todas as requisições. Toda função de `models.py` chamava `get_db()` sem
parâmetro, o que impede trocar a origem dos dados e impede exercitar a função
sem subir o banco. `controllers.py` acessava o driver do banco diretamente, sem
passar pela camada de modelo.

**Falta de coesão.** `models.py` continha funções de produto, usuário, pedido e
relatório no mesmo arquivo. Cinco motivos distintos para alterar o mesmo arquivo:
mudança no catálogo de produtos, no cadastro de usuários, na regra de estoque, na
política de desconto e no esquema do banco.

Classificação: 10 CRITICAL, 6 HIGH, 7 MEDIUM, 6 LOW.

Os problemas de maior severidade, com o motivo de cada um ser relevante:

| Severidade | Problema | Consequência verificável |
|---|---|---|
| CRITICAL | SQL montado por concatenação de string | Entrada do cliente altera a estrutura da consulta e permite ler ou apagar dados fora do escopo do endpoint |
| CRITICAL | `POST /admin/query` executa SQL vindo do corpo | Concede ao cliente a capacidade da conta de banco inteira |
| CRITICAL | `POST /admin/reset-db` apaga as tabelas sem autenticação | Qualquer cliente com acesso de rede remove todos os dados |
| CRITICAL | Senha persistida em texto puro e comparada por igualdade | O vazamento de uma cópia do banco entrega as credenciais utilizáveis |
| CRITICAL | Senha devolvida no corpo da resposta da API | Cliente sem autenticação obtém credencial de qualquer usuário |
| CRITICAL | `SECRET_KEY` e `debug` devolvidos por `GET /health` | Expõe configuração interna sem autenticação |
| CRITICAL | Chave secreta como literal no código | Entra no histórico de versionamento e exige alterar código para rotacionar |
| CRITICAL | Modo de depuração ligado com bind em `0.0.0.0` | Console interativo do Werkzeug acessível pela rede |
| HIGH | Escrita de pedido em vários passos sem transação | Falha no meio deixa pedido sem itens ou estoque debitado sem pedido |
| HIGH | Origem cruzada liberada para qualquer origem | Página de terceiro emite requisição autenticada pelo navegador |

### Projeto 2: ecommerce-api-legacy

Três arquivos, 180 linhas, densidade alta de responsabilidades por linha.

**Falta de organização.** A classe `AppManager` concentrava criação de esquema,
carga inicial, consultas, regra de pagamento, registro de rotas e montagem de
resposta. O arquivo `utils.js` reunia objeto de configuração, cache global,
função de digest e cálculo de faturamento.

**Acoplamento.** O construtor executava `new sqlite3.Database(':memory:')`, o que
prende a política ao driver concreto e impede substituir a fonte de dados. O
fluxo de checkout tinha cinco níveis de callback aninhado, com `const self = this`
para recuperar o contexto, e tratamento de erro divergente por nível.

**Falta de coesão.** Uma classe cobria cursos, usuários, matrículas, pagamentos e
registro de auditoria. Acrescentar um meio de pagamento e acrescentar um campo de
curso exigiam editar o mesmo arquivo.

Classificação: 5 CRITICAL, 8 HIGH, 7 MEDIUM, 4 LOW.

| Severidade | Problema | Consequência verificável |
|---|---|---|
| CRITICAL | Número de cartão e chave do gateway impressos no log | Dado de pagamento em canal não configurável, sem como suprimir |
| CRITICAL | Credenciais de produção como literal no código | Quatro segredos no histórico de versionamento |
| CRITICAL | Digest de senha por concatenação de base64 sem sal | O laço de 10000 iterações repete um valor derivado do início da senha e não acrescenta resistência |
| CRITICAL | Operações administrativas sem verificação de identidade | Cliente anônimo remove usuário e lê relatório financeiro |
| HIGH | Checkout escreve em quatro tabelas sem transação | Falha no meio deixa matrícula sem pagamento |
| HIGH | Remoção de usuário deixa matrículas e pagamentos órfãos | Registros apontam para identificador inexistente |
| HIGH | Cache global sem limite nem expiração | Cresce enquanto o processo viver |

### Projeto 3: task-manager-api

Único dos três com separação parcial de camadas. Possuía `models/`, `routes/`,
`services/` e `utils/`, o que não significa que a arquitetura estivesse adequada.

**Falta de organização.** Faltavam `config/`, `controllers/` e `middlewares/`.
Os três arquivos de `routes/` somavam 733 linhas e reuniam definição de rota,
acesso a dados por ORM, regra de negócio e formatação de saída. A configuração
existia como literal dentro de `app.py`, que também definia duas rotas e criava
o esquema no corpo do módulo, executando isso em todo import.

**Acoplamento.** Os três arquivos de rota importavam `db` e os modelos
diretamente e chamavam persistência dentro do handler, sem camada intermediária.
`NotificationService` instanciava `smtplib.SMTP` dentro do método, o que impede
exercitar a regra de notificação sem abrir conexão real.

**Falta de coesão.** `report_routes.py` cobria dois domínios, relatórios e
categorias. A regra de atraso estava escrita por extenso em cinco handlers, em
três arquivos, enquanto `Task.is_overdue()` implementava exatamente a mesma
regra e não era chamado em lugar nenhum. `utils/helpers.py` definia sete
constantes com os valores que os handlers repetiam como literal, e nenhuma era
importada.

Classificação: 9 CRITICAL, 11 HIGH, 20 MEDIUM, 13 LOW.

| Severidade | Problema | Consequência verificável |
|---|---|---|
| CRITICAL | Senha com MD5 sem sal e comparação por igualdade direta | Digest recuperável por tabela pré-computada; senhas iguais produzem digests iguais |
| CRITICAL | `User.to_dict()` inclui a chave `password` | Quatro endpoints devolvem o digest a cliente sem autenticação |
| CRITICAL | Três endpoints `DELETE` sem verificação de identidade | `DELETE /users/1` remove o usuário e todas as tarefas dele |
| CRITICAL | Três arquivos de rota concentram dados, regra e roteamento | Mudança de fórmula e mudança de rota tocam o mesmo arquivo |
| CRITICAL | Chave secreta e credenciais de SMTP como literal | Segredos no histórico de versionamento |
| CRITICAL | `debug=True` com bind em `0.0.0.0` | Console interativo do Werkzeug acessível pela rede |
| HIGH | Origem cruzada liberada para qualquer origem | Combinada com os `DELETE` abertos, permite remoção disparada por página de terceiro |
| HIGH | Onze blocos `except` sem tipo ou sem registro da causa | Diagnóstico em produção limitado ao código de status |
| MEDIUM | 24 usos de `datetime.utcnow()` e 66 de `Model.query` | Símbolos depreciados e legados nas versões declaradas |

---

## B) Construção da Skill

### Estrutura

O `SKILL.md` tem 398 linhas e contém apenas o procedimento: regras permanentes,
ordem das fases, formato dos blocos impressos e o portão de confirmação. O
conhecimento de domínio fica em 9 arquivos de referência, carregados no momento
em que cada fase precisa deles.

| Arquivo | Conteúdo |
|---|---|
| `stack-detection.md` | Tabelas de sinais por linguagem e framework, inventário de rotas, definição do escopo de código-fonte |
| `mvc-architecture.md` | Tabela `contém / não contém` por camada, regra de dependência, preservação do ponto de entrada |
| `antipattern-catalog.md` | 27 entradas com sinal de detecção buscável, severidade e transformação |
| `solid-principles.md` | Sinal de detecção e severidade por princípio, com par antes e depois |
| `deprecated-apis.md` | Símbolos obsoletos com versão de depreciação e substituto oficial |
| `refactoring-playbook.md` | 23 transformações, cada uma com gatilho, par antes e depois, e verificação obrigatória |
| `remediation-protocol.md` | Identidade da constatação, vocabulário de destino, registro de remediação, reconciliação |
| `audit-report-template.md` | Formato fixo do relatório de auditoria |
| `validation-protocol.md` | Captura de linha de base, comparação e critério de aprovação |
| `scripts/compare.py` | Comparador determinístico de duas capturas HTTP |

A separação entre procedimento e conhecimento existe porque o `SKILL.md` é lido
em toda execução, enquanto uma referência como `deprecated-apis.md` só é lida no
passo 2.3. Carregar tudo de uma vez consumiria contexto sem uso.

### Decisões de design

**Identificador próprio por constatação.** O identificador do catálogo se repete
dentro de um mesmo relatório: duas ocorrências de senha em texto puro são duas
constatações `C5`. Sem chave única não existe lista de portão confiável nem
registro rastreável. Cada constatação recebe `F01`, `F02` e assim por diante, na
ordem final do relatório.

**Campo `Locations:` para constatação que alcança vários arquivos.** Um literal
de segredo costuma aparecer em mais de um ponto. Corrigir um ponto e declarar a
constatação resolvida é a forma mais comum de correção parcial. O registro abre
uma linha por localização, e a constatação só fecha quando todas fecham.

**Registro de remediação com reconciliação aritmética.** Toda constatação termina
com um destino declarado, verificado e impresso: `CORRIGIDA`, `MITIGADA` ou
`NÃO APLICADA`. Três identidades precisam fechar no final: linhas do registro
igual à soma das localizações, constatações distintas igual ao total do
relatório, linhas sem destino igual a zero. A conferência é aritmética, não
julgamento.

**Destino `MITIGADA`.** Algumas transformações preservam o comportamento atual
como padrão, e quando esse valor é a condição insegura, a estrutura muda mas o
achado permanece. Chamar isso de corrigido faria um achado de segurança sair do
relatório sem sair do código.

**Portão com custo explícito.** O portão informa quantas constatações e de que
severidade permanecem no código em cada opção. Resposta afirmativa ambígua como
`sim` ou `ok` não seleciona entre aplicar tudo e aplicar apenas o que preserva o
contrato, e nesse caso a skill pergunta uma única vez de novo em vez de adotar o
mínimo por omissão.

**Arquivo `expected.json`.** Toda correção autorizada que altera o contrato
produz divergência entre a captura antes e depois. Sem declaração prévia, o
comparador reprova exatamente a mudança que o usuário mandou fazer, e a fase de
refatoração passa a ter incentivo invertido: não aplicar a correção é o caminho
que passa na validação. O comparador usa o arquivo nos dois sentidos, e uma
divergência declarada que não ocorreu também reprova, o que detecta correção
autorizada e não aplicada.

**Escopo de código-fonte definido uma vez.** A skill é copiada para dentro de
cada projeto, então uma busca por literal encontra os exemplos da própria skill.
Medido em execução real: buscar o literal `minha-chave-super-secreta-123` na
árvore sem escopo devolve cinco ocorrências, sendo três em `references/`, uma no
relatório e apenas uma no código do projeto.

### Anti-patterns incluídos e critério

O catálogo tem 27 entradas distribuídas em quatro níveis: C1 a C8 em CRITICAL,
H1 a H8 em HIGH, M1 a M6 em MEDIUM, L1 a L5 em LOW.

O critério de inclusão foi ter sinal de detecção buscável no código, independente
de projeto, e consequência verificável. Uma entrada como "código ruim" não entra
porque não é acionável. Uma entrada como "chamada de `execute` seguida de
operador de concatenação" entra porque a busca é mecânica e o resultado é binário.

As entradas de CRITICAL cobrem as classes que impedem funcionamento correto ou
expõem dado sensível: injeção de SQL, segredo embutido, execução de comando
arbitrário, operação destrutiva sem autenticação, digest inadequado de senha,
dado sensível na resposta, módulo com múltiplas responsabilidades e modo de
depuração ativo. As de HIGH cobrem violação forte de MVC e SOLID. As de MEDIUM
cobrem duplicação, gargalo de desempenho e API obsoleta. As de LOW cobrem
legibilidade e literal solto.

Cada entrada aponta para uma transformação do playbook, e cada transformação tem
bloco de verificação obrigatório. Transformação sem verificação executada não
recebe o destino `CORRIGIDA`.

### Como a skill é agnóstica de tecnologia

Nenhuma decisão de stack está no `SKILL.md`. Toda tabela que nomeia arquivo de
manifesto, símbolo de framework ou comando de boot fica nas referências.

A detecção segue ordem de precedência fixa: manifesto de dependências, extensão
predominante, importações no ponto de entrada, conteúdo dos arquivos. Nome de
diretório isolado nunca decide, porque um diretório chamado `models/` não prova
que existe camada de modelo, condição observada no projeto 3.

Para stack fora das tabelas existe um procedimento genérico com seis parâmetros
lidos do projeto: comando de boot, URL base, porta, comando de instalação,
artefato de estado e padrão de parada. A execução não é interrompida por stack
desconhecida, apenas por ausência de comando de boot ou de porta, porque sem
esses dois não há validação.

A estrutura alvo é a mesma nas três stacks: cinco diretórios de camada mais o
ponto de entrada, com a nomenclatura idiomática da linguagem. O projeto 2 usa
`routes/` e o projeto 3 usa `views/` porque essa é a convenção de cada
ecossistema, e a tabela de convenção registra a equivalência.

### Desafios encontrados e resolução

**Constatação que desaparece em silêncio.** Uma constatação que ninguém corrige e
ninguém menciona não produz erro: o relatório continua correto, a validação
continua aprovando e o bloco final continua sendo impresso. A resolução foi o
protocolo de remediação com registro semeado antes de aplicar, uma linha por
localização, e reconciliação aritmética no fechamento.

**Correção reclassificada durante a refatoração.** Descobrir na fase de
refatoração que uma correção altera o contrato é legítimo. Resolver isso sozinho
não é. O protocolo determina parar, registrar a reclassificação e voltar com um
portão estreito. Descartar a correção com base na própria reclassificação é o
caminho pelo qual uma constatação some sem que ninguém decida.

**Tratador central de erro capturando exceções de HTTP.** Um tratador registrado
para `Exception` também casa com as exceções de roteamento, porque o Flask
percorre a hierarquia de classes ao procurar o tratador. Sem a guarda
`isinstance(exc, HTTPException)`, um caminho inexistente passa a devolver 500 em
vez de 404. A guarda virou requisito explícito da transformação T11, com a tabela
de medição dos três casos.

**Porta ocupada invalidando a captura.** No macOS, a porta 5000 é ocupada por
padrão pelo receptor AirPlay, que responde 403 a qualquer caminho. Uma captura
feita nessas condições sai com 403 em todas as entradas e a comparação aprova
duas capturas igualmente inválidas. O passo 1.2 do protocolo passou a interromper
a execução, e o passo 1.6 lista três sinais de captura inválida.

**Banco resolvido na pasta de instância.** Em Flask-SQLAlchemy 3.x, a URI
`sqlite:///tasks.db` aparece em `instance/tasks.db`, não na raiz do projeto. Um
`rm -f tasks.db` na raiz não apaga nada e o boot seguinte reaproveita o banco
antigo, o que faz a linha de base partir de estado desconhecido. O passo 1.3
passou a localizar o artefato por busca, exigindo exatamente uma ocorrência.

---

## C) Resultados

### Findings por severidade

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| code-smells-project, primeira execução | 10 | 6 | 7 | 6 | 29 |
| code-smells-project, segunda execução | 6 | 2 | 5 | 2 | 15 |
| ecommerce-api-legacy | 5 | 8 | 7 | 4 | 24 |
| task-manager-api | 9 | 11 | 20 | 13 | 53 |
| task-manager-api, adendo da re-auditoria | 0 | 1 | 2 | 0 | 3 |
| Soma | 30 | 28 | 41 | 25 | 124 |

As três constatações do adendo não foram encontradas na Fase 2. Apareceram na
passagem B da re-auditoria do passo 3.5, já sobre o código refatorado, e foram
confirmadas por leitura do commit 6d1ce62 como pré-existentes ao código
original. Estão no relatório em seção separada, depois do rodapé da Fase 2,
para que o total da Fase 2 continue sendo o que a Fase 2 produziu.

Relatórios completos em [reports/audit-project-1.md](reports/audit-project-1.md),
[reports/audit-project-2.md](reports/audit-project-2.md) e
[reports/audit-project-3.md](reports/audit-project-3.md).

### Comparação antes e depois

**code-smells-project**

```
antes                        depois
app.py                       app.py                    (carregador)
controllers.py               src/app.py                (composition root)
models.py                    src/config/               settings, database, logging_config
database.py                  src/models/               produto, usuario, pedido, relatorio, admin
                             src/controllers/          produto, usuario, pedido, relatorio, admin, home
                             src/views/routes.py       19 rotas
                             src/middlewares/          error_handler
4 arquivos, 780 linhas       24 arquivos, 809 linhas
```

**ecommerce-api-legacy**

```
antes                        depois
src/app.js                   src/app.js                (ponto de entrada preservado)
src/AppManager.js            src/container.js          (composição de dependências)
src/utils.js                 src/config/               settings, db, logger
                             src/models/               course, user, enrollment, payment, audit, checkout, report, schema, password
                             src/controllers/          checkout, report, user, httpError
                             src/routes/index.js       3 rotas
                             src/middlewares/          adminGuard, errorHandler, envelope
3 arquivos, 180 linhas       22 arquivos, 969 linhas
```

**task-manager-api**

```
antes                        depois
app.py                       app.py                    (carregador)
database.py                  src/app.py                (composition root)
models/  (3 entidades)       src/config/               settings, database, clock, logging_config
routes/  (3 arquivos)        src/models/               user, category, task, report
services/notification_...    src/controllers/          task, user, category, report, health, validators, envelope
utils/helpers.py             src/views/routes.py       22 rotas
                             src/middlewares/          error_handler, admin_guard
15 arquivos, 1158 linhas     27 arquivos, 1597 linhas
```

Os diretórios `models/`, `routes/`, `services/` e `utils/` do projeto 3 não foram
preservados por padrão. Cada arquivo foi classificado pelo conteúdo contra a
tabela `contém / não contém` e movido para a camada correspondente.

### Checklist de validação

**Fase 1, análise**

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Linguagem detectada corretamente | Python | JavaScript (Node.js) | Python |
| Framework detectado corretamente | Flask 3.1.1 | Express ^4.18.2 | Flask 3.0.0 |
| Domínio descrito corretamente | API de e-commerce | LMS com checkout | Task Manager |
| Número de arquivos condiz | 4 | 3 | 15 |

**Fase 2, auditoria**

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Relatório segue o template | Sim | Sim | Sim |
| Cada finding tem arquivo e linhas exatos | Sim | Sim | Sim |
| Findings ordenados por severidade | Sim | Sim | Sim |
| Mínimo de 5 findings | 29 | 24 | 53 |
| Detecção de APIs deprecated incluída | Sem ocorrência no relatório | Sem ocorrência no relatório | 24 usos de `datetime.utcnow`, 66 de `Model.query` |
| Skill pausa e pede confirmação | Sim | Sim | Sim |

**Fase 3, refatoração**

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Estrutura segue padrão MVC | Sim, 5 camadas | Sim, 5 camadas | Sim, 5 camadas |
| Configuração em módulo de config | `src/config/settings.py` | `src/config/settings.js` | `src/config/settings.py` |
| Models abstraem dados | 5 módulos | 9 módulos | 4 módulos |
| Views ou routes separadas | `src/views/routes.py` | `src/routes/index.js` | `src/views/routes.py` |
| Controllers concentram o fluxo | 6 módulos | 4 módulos | 7 módulos |
| Error handling centralizado | `error_handler.py` | `errorHandler.js` | `error_handler.py` |
| Entry point claro | `app.py` | `src/app.js` | `app.py` |
| Aplicação inicia sem erros | Sim | Sim | Sim |
| Endpoints originais respondem | 19 rotas | 3 rotas | 22 rotas |

### Logs de execução após a refatoração

Coletados executando o comando de boot documentado de cada projeto.

#### Projeto 1, code-smells-project, python app.py
```
2026-09-07 19:46:10,809 INFO __main__ ==================================================
2026-09-07 19:46:10,809 INFO __main__ SERVIDOR INICIADO
2026-09-07 19:46:10,809 INFO __main__ Rodando em http://localhost:5000
GET /                      -> 200
GET /health                -> 200
GET /produtos              -> 200
GET /usuarios              -> 200
GET /relatorios/vendas     -> 200
POST /admin/reset-db       -> 200
```

#### Projeto 2, ecommerce-api-legacy, npm start
```
> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node src/app.js
[INFO] Frankenstein LMS rodando na porta 3000...
GET /api/admin/financial-report    -> 401 (sem credencial)
POST /api/checkout                 -> 400 (corpo vazio)
DELETE /api/users/1                -> 401 (sem credencial)
```

#### Projeto 3, task-manager-api, python app.py
```
 * Serving Flask app 'src.app'
 * Debug mode: off
2026-09-07 19:46:25,415 INFO werkzeug WARNING: This is a development server.
GET /                      -> 200
GET /health                -> 200
GET /tasks                 -> 200
GET /tasks/stats           -> 200
GET /users                 -> 200
GET /categories            -> 200
GET /reports/summary       -> 200
DELETE /tasks/1            -> 401 (sem credencial)
PUT /users/1               -> 401 (sem credencial)
```

### Estado residual por projeto

O portão da Fase 2 recebeu respostas diferentes em cada projeto, e isso produz
estados finais diferentes. O registro abaixo descreve o que permanece no código.

**Projeto 1.** A primeira execução deixou as correções `[contract-breaking]`
recusadas no portão, e o código as registrava em comentário. A skill foi
executada uma segunda vez sobre o estado já refatorado, com o portão respondido
`a`, e as 15 constatações da nova auditoria foram aplicadas.

Antes da segunda execução, verificado por execução:

```
POST /admin/query com {"sql":"SELECT nome, email, senha FROM usuarios LIMIT 2"}
  -> 200 {"dados":[{"email":"admin@loja.com","nome":"Admin","senha":"admin123"}, ...]}
POST /admin/reset-db sem credencial -> 200
GET /usuarios                       -> chave senha presente, em texto puro
GET /health                         -> chaves debug e secret_key presentes
```

Depois:

```
POST /admin/query                   -> 404, a rota foi removida
POST /admin/reset-db sem credencial -> 401, com credencial válida -> 200
GET /usuarios                       -> criado_em, email, id, nome, tipo
GET /health                         -> ambiente, counts, database, db_path, status, versao
banco recriado                      -> pbkdf2_sha256$240000$...
```

Nenhuma constatação do projeto 1 permanece sem correção. O registro fecha com
29 linhas, 15 constatações distintas e nenhuma sem destino.

**Projeto 2.** As 24 constatações foram aplicadas, incluindo as 5 que alteram o
contrato. Os dois endpoints administrativos passaram a exigir credencial, e as
senhas passaram a `pbkdf2-sha256` com sal por usuário.

**Projeto 3.** As 53 constatações da Fase 2 foram aplicadas, incluindo as 8 que
alteram o contrato. A re-auditoria encontrou 9 defeitos introduzidos pela
própria refatoração, todos corrigidos antes da conclusão, entre eles
`hmac.compare_digest` sobre texto devolvendo 500 para token com caractere fora
de ASCII e o corpo do 500 devolvendo a consulta SQL ao cliente.

A re-auditoria encontrou também 3 constatações pré-existentes que a Fase 2 não
havia reportado. As três alteram o contrato, foram levadas a um portão estreito,
autorizadas e aplicadas:

| F | Correção | Verificação |
|---|---|---|
| F54 | `PUT /users/<id>` passa a exigir credencial administrativa | sem cabeçalho devolve 401, com `X-Admin-Token` válido devolve 200 |
| F55 | `PUT /categories/<id>` passa a recusar corpo vazio ou nulo | corpo `{}` e corpo `null` passam de 200 e 500 para 400 |
| F56 | os sete handlers de escrita passam a exigir corpo objeto | `POST /tasks` com `"abc"` e `PUT /users/1` com `[1,2]` passam de 500 e 200 para 400 |

Nenhuma constatação do projeto 3 permanece sem correção. O registro fecha com
95 linhas, 56 constatações distintas e nenhuma sem destino.

### Comportamento da skill em stacks diferentes

**A detecção de stack usou o manifesto, não o nome do diretório.** No projeto 3,
a presença de `models/`, `routes/`, `services/` e `utils/` poderia sugerir
camadas implementadas. A classificação aplicou os dois eixos previstos,
existência de diretório e pureza de cada camada, e resultou em `camadas parciais`
porque os três arquivos de `routes/` continham acesso a dados e regra de negócio.

**O volume de constatações não acompanhou o tamanho do projeto.** O projeto 2 tem
180 linhas e 24 constatações, uma a cada 7,5 linhas. O projeto 3 tem 1158 linhas
e 53 constatações, uma a cada 21,8 linhas. A densidade maior no projeto menor vem
de uma classe única concentrar cinco responsabilidades.

**As transformações aplicadas foram diferentes por projeto.** T8, que lineariza
callbacks aninhados, só teve gatilho no projeto 2. T1, que substitui consulta
concatenada por consulta parametrizada, teve gatilho no projeto 1 e nenhum no
projeto 3, porque o projeto 3 usa ORM. T17, que troca o digest de senha, teve
gatilho nos três, com implementação diferente em Python e em Node.js, ambas sem
dependência nova.

**A validação por comparação de capturas funcionou nas duas stacks.** O
comparador conhece apenas método, caminho, código de status e corpo, o que é
comum a qualquer aplicação que fale HTTP. No projeto 2 a comparação revelou que a
ordem dos arrays do relatório não era contrato: três capturas do código original
discordaram entre si. No projeto 3 a comparação em duas etapas detectou uma
regressão introduzida pela refatoração, um conversor de rota declarado como
`cat_id` enquanto o controller nomeava o parâmetro `category_id`, que fazia todo
`PUT /categories/<id>` devolver 500.

**O banco em memória do projeto 2 exigiu tratamento distinto.** Com
`:memory:`, cada conexão nova cria um banco vazio, então a instância única passou
a ser criada no container e compartilhada. Nos projetos 1 e 3, com banco em
arquivo, a linha de base foi capturada a partir de uma cópia do arquivo.

---

## D) Como Executar

### Pré-requisitos

| Requisito | Uso |
|---|---|
| Claude Code instalado e configurado | Executa a skill |
| Python 3.9 ou superior | Projetos 1 e 3 |
| Node.js 18 ou superior | Projeto 2 |
| `curl` e `lsof` | Captura e verificação de porta durante a validação |

A porta 5000 precisa estar livre para os projetos 1 e 3, e a 3000 para o projeto
2. No macOS, desligar o Receptor AirPlay em Ajustes do Sistema, Geral, AirDrop e
Handoff, porque ele ocupa a porta 5000 por padrão.

### Executar a skill

A skill já está copiada em `.claude/skills/refactor-arch/` dentro dos três
projetos. Para executar:

```bash
cd code-smells-project
claude "/refactor-arch"

cd ../ecommerce-api-legacy
claude "/refactor-arch"

cd ../task-manager-api
claude "/refactor-arch"
```

A execução para no portão da Fase 2 e aguarda resposta antes de alterar qualquer
arquivo. As opções são `a` para aplicar todas as correções, `s` para aplicar
apenas as que preservam o contrato, números para selecionar itens específicos e
`n` para encerrar sem alterar nada.

O relatório da Fase 2 é gravado em `reports/audit-<nome-do-projeto>.md` dentro do
projeto. Para o entregável, copiar para `reports/audit-project-{1,2,3}.md` na
raiz do repositório.

### Validar que a refatoração funcionou

**Projeto 1 e projeto 3**, Python:

```bash
cd code-smells-project        # ou task-manager-api
pip install -r requirements.txt
python seed.py                # apenas no projeto 3
python app.py
```

Em outro terminal:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5000/
curl -s http://127.0.0.1:5000/produtos   # projeto 1
curl -s http://127.0.0.1:5000/tasks      # projeto 3
```

**Projeto 2**, Node.js:

```bash
cd ecommerce-api-legacy
npm ci
npm start
```

Em outro terminal:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/api/admin/financial-report
```

O retorno 401 é o esperado, porque a rota passou a exigir credencial.

**Comparar o comportamento antes e depois.** A skill grava os artefatos de
validação em `.refactor-arch/` dentro do projeto, fora do versionamento. Para
reexecutar a comparação:

```bash
python3 .claude/skills/refactor-arch/scripts/compare.py \
  .refactor-arch/baseline.json .refactor-arch/after.json \
  --expected .refactor-arch/expected.json
```

Códigos de saída: 0 quando não há divergência não autorizada e toda divergência
declarada foi observada, 1 quando há divergência não autorizada ou declarada e
não observada, 2 quando a captura está ausente ou inválida.
