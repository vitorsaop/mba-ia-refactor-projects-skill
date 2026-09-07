================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2 (4.22.1 travada em package-lock.json)
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 8 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Classe única concentra esquema, dados, regra e roteamento (F01, C7)
File: src/AppManager.js:1-141
Description: A classe AppManager instancia o driver do banco (linha 7), cria o esquema e a carga inicial (linhas 12-21), registra as três rotas (linhas 28, 80, 131), aplica a regra de aprovação de pagamento (linha 46), executa consultas e escritas (linhas 37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133) e monta corpo e código de status de cada resposta (linhas 35, 38, 41, 48, 51, 55, 60, 84, 87, 98, 121, 135). Seis responsabilidades no mesmo arquivo. Viola também SRP.
Impact: Nenhuma parte pode ser exercitada sem subir o servidor HTTP e o banco. Uma mudança no esquema, na regra de pagamento ou no formato do relatório edita o mesmo arquivo.
Recommendation: Separar em config, models, controllers, routes e middlewares, e reduzir o ponto de entrada à composição. Aplicar T3 e T15.

### [CRITICAL] Número de cartão e chave do gateway impressos no log (F02, C6)
File: src/AppManager.js:45
Description: A linha imprime `Processando cartão ${cc} na chave ${config.paymentGatewayKey}` na saída padrão. `cc` é o campo `card` recebido em POST /api/checkout, sem mascaramento.
Impact: O número completo do cartão e a chave do gateway ficam na saída do processo e em qualquer coletor que a capture. Não existe nível de log que suprima essa linha.
Recommendation: Remover o número do cartão e a chave do conteúdo registrado, e passar o registro por um módulo de log com nível. Aplicar T23; o literal da chave sai do código por T2.

### [CRITICAL] Operações administrativas sem verificação de identidade (F03, C4) [contract-breaking]
File: src/AppManager.js:80-129,131-137
Description: DELETE /api/users/:id executa `DELETE FROM users WHERE id = ?` (linha 133) sem nenhuma verificação de identidade ou permissão. GET /api/admin/financial-report (linha 80) devolve o faturamento por curso e a lista de alunos de cada curso, também sem verificação. O projeto não registra middleware de autenticação em lugar algum.
Impact: Qualquer cliente com acesso de rede apaga usuários e lê o relatório financeiro completo.
Recommendation: Proteger os dois endpoints com verificação de credencial administrativa por cabeçalho, com comparação em tempo constante. Aplicar T16, opção B (proteção), recomendada pelo playbook para o gatilho C4.
Contract change: DELETE /api/users/:id e GET /api/admin/financial-report passam a devolver 401 quando o cabeçalho de credencial administrativa estiver ausente ou incorreto. Hoje devolvem 200 sem credencial. Com credencial válida, corpo e status permanecem idênticos.

### [CRITICAL] Credenciais de produção embutidas no código (F04, C2)
File: src/utils.js:1-7
Description: O objeto `config` atribui literais a `dbUser` ("admin_master"), `dbPass` ("senha_super_secreta_prod_123"), `paymentGatewayKey` ("pk_live_1234567890abcdef") e `smtpUser`. O prefixo `pk_live_` identifica chave de ambiente produtivo. Nenhum dos quatro valores alimenta chamada funcional: `paymentGatewayKey` aparece apenas no registro de log de src/AppManager.js:45, tratado em F02; os outros três não são referenciados em nenhum arquivo do projeto.
Impact: Os quatro valores estão no histórico de versionamento e não podem ser rotacionados sem alterar o código.
Recommendation: Remover os quatro literais. Pelos critérios de T2 são categoria C, e como o único consumidor sai por T23 e T12, saem do código sem substituto. `port` é categoria A e vira valor padrão do módulo de configuração, com o mesmo 3000. Aplicar T2. A remoção do código não revoga credencial já publicada: rotacioná-las no provedor é ação de operação, fora do alcance da refatoração.

### [CRITICAL] Senhas com digest inadequado e em texto puro (F05, C5) [contract-breaking]
File: src/utils.js:17-23
Locations: src/utils.js:17-23, src/AppManager.js:18,68-69
Description: `badCrypto` concatena 10.000 vezes os dois primeiros caracteres de `Buffer.from(pwd).toString('base64')` e devolve os 10 primeiros caracteres do resultado (src/utils.js:17-23). O laço repete sempre o mesmo par, portanto a saída é a repetição de um valor derivado do início da senha, sem sal. O valor é gravado na coluna `pass` em src/AppManager.js:69. A carga inicial grava a senha '123' em texto puro em src/AppManager.js:18. Quando `pwd` está ausente, a senha usada é o literal "123456" (src/AppManager.js:68).
Impact: O valor armazenado é reversível por tabela pré-computada sobre os dois primeiros caracteres da senha. Duas senhas com o mesmo início produzem o mesmo valor armazenado. As 10.000 iterações não acrescentam resistência.
Recommendation: Substituir por `crypto.pbkdf2` com sal por usuário, da biblioteca padrão do Node, e gravar a senha da carga inicial pelo mesmo caminho. Aplicar T17.
Contract change: As senhas já persistidas deixam de validar. O valor da coluna `pass` muda de formato para o usuário da carga inicial e para todo usuário criado por POST /api/checkout. Nenhum endpoint atual expõe ou verifica senha, portanto a mudança não é observável por HTTP.

### [HIGH] Driver do banco instanciado dentro da classe (F06, H4)
File: src/AppManager.js:1,7
Description: `require('sqlite3').verbose()` é resolvido no carregamento do módulo (linha 1) e `new sqlite3.Database(':memory:')` é executado no construtor (linha 7). O caminho do banco é o literal `':memory:'`. Viola também DIP.
Impact: Não há como exercitar a classe sem criar um banco SQLite, nem trocar a origem dos dados sem editar o construtor. O literal `':memory:'` impede apontar para outro banco por configuração.
Recommendation: Instanciar o driver em um container chamado apenas pelo ponto de entrada e injetar a conexão nos models. Mover o literal para o módulo de configuração como categoria A, com o mesmo valor padrão. Aplicar T6 e T2.

### [HIGH] Cinco níveis de callback aninhado no checkout (F07, H5)
File: src/AppManager.js:26,37-77
Description: O handler de POST /api/checkout aninha `db.get` (linha 37), `db.get` (linha 40), `db.run` (linha 50), `db.run` (linha 54) e `db.run` (linha 57). A linha 26 declara `const self = this` porque as linhas 50 e 54 usam `function(err)` para alcançar `this.lastID`, o que troca o `this` do bloco. Cada nível tem o seu próprio caminho de erro (linhas 38, 41, 51, 55).
Impact: O caminho de sucesso está distribuído por cinco blocos. O callback da linha 57 responde 200 mesmo quando a gravação da auditoria falha, porque não testa `err`.
Recommendation: Envolver as chamadas do driver em promessas e linearizar o fluxo com async/await no controller, preservando a ordem das operações. Aplicar T8.

### [HIGH] Camada de controller inexistente (F08, H2)
File: src/AppManager.js:28-137
Description: Os três handlers registrados em `setupRoutes` leem a requisição, chamam o driver do banco diretamente e montam a resposta no mesmo bloco. Não existe camada entre a definição de rota e o acesso a dados.
Impact: Nenhum fluxo de requisição pode ser exercitado sem construir uma requisição HTTP. Não há ponto único para validação de entrada nem para montagem de resposta.
Recommendation: Extrair um controller por domínio e reduzir a camada de rotas à associação entre caminho, método e controller. Aplicar T4 e T5.

### [HIGH] Regra de negócio dentro dos handlers de rota (F09, H1)
File: src/AppManager.js:46,86-121
Description: A regra de aprovação de pagamento está na linha 46: `cc.startsWith("4") ? "PAID" : "DENIED"`. A agregação do relatório financeiro está nas linhas 86-121: contagem de pendências, soma de `payment.amount` quando `payment.status === 'PAID'` (linhas 108-110) e montagem da lista de alunos (linhas 112-115).
Impact: A regra de aprovação e o cálculo de faturamento não podem ser reutilizados nem exercitados sem emitir uma requisição HTTP.
Recommendation: Mover a regra de aprovação para um model de pagamento e a agregação para um model de relatório, preservando o prefixo "4", os rótulos "PAID" e "DENIED" e a fórmula da soma. Aplicar T5.

### [HIGH] Checkout escreve em quatro tabelas sem transação (F10, H6)
File: src/AppManager.js:50-63,69-72
Description: Uma requisição de checkout executa até quatro escritas relacionadas: INSERT em `users` (linha 69), INSERT em `enrollments` (linha 50), INSERT em `payments` (linha 54) e INSERT em `audit_logs` (linha 57). Não há `BEGIN`, `COMMIT` nem `ROLLBACK` no caminho.
Impact: Falha na linha 54 deixa uma matrícula sem pagamento; falha na linha 57 deixa a operação sem registro de auditoria. Os caminhos de erro das linhas 51 e 55 respondem 500 e não desfazem as escritas anteriores.
Recommendation: Envolver a sequência em uma transação, com `COMMIT` no sucesso e `ROLLBACK` no erro. Aplicar T9.

### [HIGH] Erro de banco recebido e descartado (F11, H7)
File: src/AppManager.js:57,92,104,106,133
Description: Cinco callbacks recebem `err` e não o testam nem o registram. A linha 57 responde 200 mesmo com falha na gravação da auditoria. A linha 92 acessa `enrollments.length` sem verificar `err`. As linhas 104 e 106 ignoram o erro e o aluno entra no relatório como 'Unknown' com valor pago 0. A linha 133 responde sucesso mesmo quando a remoção falha.
Impact: A causa de uma falha de banco não aparece em lugar algum. Uma falha na consulta da linha 92 lança TypeError dentro de um callback do driver, fora do ciclo de requisição do Express, o que derruba o processo.
Recommendation: Testar `err` em cada callback e propagá-lo a um tratador central registrado no ponto de entrada. Aplicar T11.

### [HIGH] Remoção de usuário deixa matrículas e pagamentos órfãos (F12, H6) [contract-breaking]
File: src/AppManager.js:131-137
Description: DELETE /api/users/:id executa apenas `DELETE FROM users WHERE id = ?` (linha 133). As linhas de `enrollments` e de `payments` que referenciam o usuário permanecem. O corpo da resposta declara isso na linha 135: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.". A constatação é separada de F10 porque o defeito é outro: ali falta transação, aqui faltam as escritas dependentes.
Impact: Depois de uma remoção, GET /api/admin/financial-report continua somando o pagamento do usuário removido no faturamento do curso e lista o aluno como 'Unknown' (linha 113).
Recommendation: Remover, na mesma transação, as linhas dependentes de `payments` e de `enrollments` antes da linha de `users`. Aplicar T9.
Contract change: DELETE /api/users/:id passa a apagar também as linhas de `enrollments` e de `payments` associadas ao usuário. Em consequência, GET /api/admin/financial-report executado depois de uma remoção deixa de contar o pagamento e o aluno correspondentes.

### [HIGH] Estado global mutável sem limite nem expiração (F13, H3)
File: src/utils.js:9-10,14,25
Locations: src/utils.js:9-10,14,25, src/AppManager.js:2,59
Description: `globalCache` é um objeto de módulo (src/utils.js:9) mutado por `logAndCache` (src/utils.js:14) a cada checkout bem-sucedido (src/AppManager.js:59), com uma chave por usuário e sem remoção. `totalRevenue` é variável de módulo (src/utils.js:10) exportada por valor (src/utils.js:25). Nenhum arquivo do projeto lê qualquer um dos dois.
Impact: O objeto cresce enquanto o processo viver, com uma entrada por usuário que fez checkout, e nenhum consumidor lê o que foi guardado.
Recommendation: Remover o cache e a variável, que não têm leitor, junto com as exportações e a chamada de src/AppManager.js:59, preservando o registro de log em nível informativo. Aplicar T6 e T12.

### [MEDIUM] Modo verboso do driver ativado incondicionalmente (F14, C8)
File: src/AppManager.js:1
Description: `require('sqlite3').verbose()` ativa o modo verboso do driver no carregamento do módulo, sem condicionamento a variável de ambiente. Nesse modo o sqlite3 captura o rastreamento de pilha na criação de cada consulta. A severidade fica em MEDIUM, e não na CRITICAL prevista por C8, porque nenhum rastreamento chega ao cliente: os handlers respondem apenas texto fixo (linhas 38, 41, 51, 55, 70, 84).
Impact: A captura de pilha ocorre em toda consulta, inclusive em produção, e não há como desligá-la sem editar o código.
Recommendation: Condicionar a chamada a uma variável de ambiente lida no módulo de configuração, com padrão desligado, como T2 prescreve para sinalizador de depuração. Aplicar T2.

### [MEDIUM] Símbolos importados e exportados sem uso (F15, M5)
File: src/AppManager.js:2
Locations: src/AppManager.js:2, src/utils.js:10,25
Description: src/AppManager.js:2 desestrutura `totalRevenue` de `./utils` e não o referencia em nenhuma linha do arquivo. src/utils.js:25 exporta `globalCache` e `totalRevenue`; nenhum arquivo do projeto lê os dois símbolos. Viola também ISP.
Impact: A leitura sugere um acumulador de faturamento compartilhado que não existe em uso.
Recommendation: Remover a importação não referenciada e as exportações sem leitor. Aplicar T12.

### [MEDIUM] Validação de entrada incompleta (F16, M3) [contract-breaking]
File: src/AppManager.js:35,46,68,132
Description: A linha 35 verifica apenas a presença de `usr`, `eml`, `c_id` e `card`. Não há verificação de tipo nem de formato. `c_id` segue para o parâmetro da consulta com qualquer tipo (linha 37). `card` é usado como texto na linha 46 sem verificação de tipo. `pwd` é opcional e, quando ausente, a senha gravada é o literal "123456" (linha 68). `eml` é persistido sem verificação de formato. Em DELETE /api/users/:id, `req.params.id` (linha 132) vai direto para a consulta.
Impact: `card` numérico faz `cc.startsWith` lançar TypeError dentro de um callback do driver, o que derruba o processo. `c_id` textual é aceito pelo SQLite e persiste matrícula. Um usuário criado sem `pwd` fica com senha conhecida.
Recommendation: Validar tipo e formato de `usr`, `eml`, `c_id`, `card` e `pwd` no controller, e o formato de `id` na remoção, devolvendo 400. Aplicar T20.
Contract change: POST /api/checkout passa a devolver 400 quando `c_id` não for inteiro, `card` não for texto de dígitos, `eml` não tiver formato de e-mail, ou `pwd` estiver ausente. Hoje `c_id` textual e `pwd` ausente são aceitos e persistidos. DELETE /api/users/:id passa a devolver 400 quando `id` não for inteiro; hoje devolve 200.

### [MEDIUM] Tratamento de erro replicado por handler (F17, M4)
File: src/AppManager.js:38,41,51,55,70,84
Locations: src/AppManager.js:38,41,51,55,70,84, src/app.js:1-14
Description: Cada caminho de erro devolve o seu próprio texto: "Curso não encontrado" (linha 38), "Erro DB" (linhas 41 e 84), "Erro Matrícula" (linha 51), "Erro Pagamento" (linha 55) e "Erro ao criar usuário" (linha 70). O ponto de entrada src/app.js não registra middleware de tratamento de erro.
Impact: O formato e o texto do erro dependem de qual bloco falhou, e cada novo endpoint precisa replicar o tratamento. Exceção não capturada chega ao tratador padrão do Express.
Recommendation: Registrar um middleware de erro no ponto de entrada e encaminhar os erros por `next(err)`, preservando os códigos de status e os textos atuais nos caminhos já tratados. Aplicar T11.

### [MEDIUM] Consultas dentro de laço no relatório financeiro (F18, M1)
File: src/AppManager.js:89-127
Description: O handler consulta os cursos (linha 83), depois as matrículas de cada curso dentro de `courses.forEach` (linha 92) e, dentro de `enrollments.forEach`, o usuário (linha 104) e o pagamento (linha 106) de cada matrícula. Com C cursos e M matrículas são 1 + C + 2xM consultas.
Impact: O número de idas ao banco cresce linearmente com o número de matrículas. Com a carga inicial já são cinco consultas para dois cursos e uma matrícula.
Recommendation: Substituir por consulta única com junção entre `courses`, `enrollments`, `users` e `payments`, agrupando em memória. Preservar a fórmula do faturamento e a ordem dos cursos observada na linha de base, que hoje resulta da ordem de conclusão dos callbacks e não da ordem de `id`. Aplicar T7.

### [MEDIUM] Bloco de conclusão do relatório duplicado (F19, M2)
File: src/AppManager.js:96-98,119-121
Description: O mesmo bloco de três instruções, `report.push(courseData)`, `coursesPending--` e `if (coursesPending === 0) res.json(report)`, aparece nas linhas 96-98 e nas linhas 119-121.
Impact: Uma correção no critério de conclusão precisa ser aplicada nos dois pontos. Um ponto esquecido deixa a requisição sem resposta.
Recommendation: Consolidar o critério em um único ponto. A consulta única de T7 e a linearização de T8 eliminam o contador e os dois blocos. Aplicar T10 junto de T7.

### [MEDIUM] Módulo fora das cinco camadas concentra configuração, estado e regra (F20, MVC)
File: src/utils.js:1-25
Description: src/utils.js não é uma das cinco camadas e falha nas três condições do teste de resíduo de mvc-architecture.md: contém objeto de configuração (linhas 1-7), estado mutável de módulo (linhas 9-10) e a derivação do valor armazenado de senha (linhas 17-23), que é regra de domínio. É importado por src/app.js e por src/AppManager.js.
Impact: Configuração, estado e regra de senha mudam por motivos diferentes e vivem no mesmo arquivo, alcançado por duas camadas distintas.
Recommendation: Classificar cada bloco pelo conteúdo e movê-lo para a camada correspondente: configuração para src/config/, derivação de senha para o model de usuário, registro de log para um módulo de log. Aplicar T3.

### [LOW] Identificadores de um e dois caracteres (F21, L2)
File: src/AppManager.js:26,29-33,89,102
Description: `self` (linha 26), `u`, `e`, `p`, `cid` e `cc` (linhas 29-33), `c` (linha 89) e `enr` (linha 102) nomeiam usuário, e-mail, senha, identificador de curso, cartão, curso e matrícula. `e` designa e-mail em um arquivo que usa `err` para erro.
Impact: O significado precisa ser reconstruído a cada leitura, e `e` e `err` convivem no mesmo escopo aninhado.
Recommendation: Renomear apenas as variáveis locais, preservando as chaves `usr`, `eml`, `pwd`, `c_id` e `card` do corpo da requisição. Aplicar T21.

### [LOW] Envelopes de resposta divergentes entre endpoints (F22, L4) [contract-breaking]
File: src/AppManager.js:35,38,60,87,98,121,135
Description: POST /api/checkout devolve JSON com as chaves `msg` e `enrollment_id` (linha 60) e texto puro nos erros (linhas 35 e 38). GET /api/admin/financial-report devolve um array puro (linhas 87, 98 e 121). DELETE /api/users/:id devolve texto puro (linha 135).
Impact: O cliente precisa de tratamento por endpoint: dois formatos de sucesso e erros sem chave.
Recommendation: A recomendação padrão de T22 é não aplicar, porque o ganho é de padronização e o custo é quebrar todos os consumidores atuais, inclusive api.http. Aplicar T22 somente se autorizado.
Contract change: Todos os endpoints passam a devolver um envelope único. GET /api/admin/financial-report deixa de devolver um array na raiz. DELETE /api/users/:id e os caminhos de erro deixam de devolver texto puro. POST /api/checkout passa a aninhar `msg` e `enrollment_id` dentro do envelope.

### [LOW] Literais de negócio sem nome (F23, L1)
File: src/AppManager.js:46,68
Locations: src/AppManager.js:46,68, src/utils.js:19,20,22
Description: O prefixo de aprovação "4" e os rótulos "PAID" e "DENIED" aparecem como literais na linha 46 de src/AppManager.js. A senha padrão "123456" aparece na linha 68. Em `badCrypto`, o número de iterações 10000 (src/utils.js:19), o recorte 2 (src/utils.js:20) e o tamanho 10 do resultado (src/utils.js:22) são literais.
Impact: O significado dos valores não é recuperável pela leitura. "PAID" aparece também na carga inicial (src/AppManager.js:21) sem ligação declarada com a linha 46.
Recommendation: Extrair para constantes nomeadas no módulo de configuração ou no model correspondente, preservando exatamente os mesmos valores. Aplicar T13.

### [LOW] console.log usado como registro de log (F24, L3)
File: src/app.js:13
Locations: src/app.js:13, src/utils.js:13
Description: `console.log` registra a subida do servidor (src/app.js:13) e a gravação no cache (src/utils.js:13), sem nível e sem destino configurável.
Impact: Não há como filtrar por severidade nem direcionar a saída para um coletor.
Recommendation: Encapsular em um módulo de log com nível, conforme o exemplo de T23 para Node.js, sem acrescentar dependência. Aplicar T23. A linha de src/utils.js:13 sai junto com a remoção do cache tratada em F13.

================================
Total: 24 findings
================================
