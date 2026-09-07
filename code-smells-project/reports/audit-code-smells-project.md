================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   24 analyzed | ~809 lines of code

## Summary
CRITICAL: 6 | HIGH: 2 | MEDIUM: 5 | LOW: 2

## Findings

### [CRITICAL] Senha persistida e comparada em texto puro (F01, C5) [contract-breaking]
File: src/config/database.py:19-23
Locations: src/config/database.py:19-23,78-81, src/models/usuario_model.py:24-31, src/models/usuario_model.py:34-40
Description: O artefato de carga inicial grava `admin123`, `123456` e `senha123` como valor da coluna `senha`. `usuario_model.login` autentica com `SELECT * FROM usuarios WHERE email = ? AND senha = ?`, comparando o texto puro dentro da consulta, e `usuario_model.create` grava o valor recebido sem transformação.
Impact: Uma cópia do banco entrega credenciais utilizáveis diretamente, sem trabalho de recuperação. A comparação dentro da consulta não é de tempo constante. Confirmado por execução: `POST /admin/query` com `SELECT nome, email, senha FROM usuarios` devolve as três senhas em texto puro.
Recommendation: Substituir por `hashlib.pbkdf2_hmac` com sal por usuário e comparação com `hmac.compare_digest`, ambos da biblioteca padrão. Aplicar T17.
Contract change: As senhas gravadas pelo artefato de carga deixam de validar. `POST /login` passa a devolver 401 para as credenciais de exemplo até o banco ser recriado. O formato do valor armazenado muda de texto puro para `pbkdf2_sha256$<iteracoes>$<sal>$<digest>`.

### [CRITICAL] Operação destrutiva sem autenticação (F02, C4) [contract-breaking]
File: src/controllers/admin_controller.py:10-13
Locations: src/controllers/admin_controller.py:10-13, src/models/admin_model.py:4-10, src/views/routes.py:40
Description: `POST /admin/reset-db` executa `DELETE FROM` nas quatro tabelas do projeto sem nenhuma verificação de identidade ou permissão no caminho de execução. Confirmado por execução: a requisição sem cabeçalho algum devolve 200 e apaga os dados.
Impact: Qualquer cliente com acesso de rede remove todos os produtos, usuários, pedidos e itens de pedido em uma requisição.
Recommendation: Proteger o endpoint com verificação de credencial administrativa em middleware, preservando a função. Aplicar T16, opção B.
Contract change: `POST /admin/reset-db` passa a devolver 401 com corpo `{"erro": "Não autorizado"}` para requisição sem o cabeçalho de credencial. Com credencial válida, corpo e status permanecem idênticos.

### [CRITICAL] Endpoint que executa comando SQL arbitrário (F03, C3) [contract-breaking]
File: src/controllers/admin_controller.py:16-25
Locations: src/controllers/admin_controller.py:16-25, src/models/admin_model.py:13-19, src/views/routes.py:41
Description: `POST /admin/query` lê a chave `sql` do corpo da requisição e a entrega a `conn.execute` sem validação, sem lista de comandos permitidos e sem autenticação. Confirmado por execução: o corpo `{"sql":"SELECT nome, email, senha FROM usuarios LIMIT 2"}` devolve 200 com as credenciais dos usuários.
Impact: Concede ao cliente anônimo a capacidade inteira da conta de banco: ler qualquer tabela, alterar qualquer registro e remover qualquer dado. Nenhuma validação de rota mitiga, porque o comando é o próprio dado de entrada.
Recommendation: Remover a rota. Proteger por token não elimina a capacidade de executar comando arbitrário, apenas restringe quem a exerce. Aplicar T16, opção A.
Contract change: `POST /admin/query` deixa de existir e passa a devolver o código que o framework usa para caminho não registrado.

### [CRITICAL] Chave secreta e sinalizador de depuração na resposta de /health (F04, C6) [contract-breaking]
File: src/controllers/relatorio_controller.py:11-25
Description: O corpo devolvido por `GET /health` inclui as chaves `debug` com o valor fixo `True` e `secret_key` com o literal `minha-chave-super-secreta-123`. O valor de `debug` não reflete a configuração em execução, que hoje é falso por padrão.
Impact: Qualquer cliente sem autenticação obtém a chave de configuração da aplicação. O endpoint de verificação de saúde é o menos protegido de um projeto, e costuma ser exposto a sondagem externa.
Recommendation: Remover as chaves `debug` e `secret_key` do corpo. Aplicar T18.
Contract change: `GET /health` deixa de devolver as chaves `debug` e `secret_key`. As demais chaves permanecem inalteradas.

### [CRITICAL] Chave secreta embutida no código (F05, C2)
File: src/controllers/relatorio_controller.py:24
Description: O literal `minha-chave-super-secreta-123` está escrito no código. O módulo de configuração já lê `SECRET_KEY` do ambiente em src/config/settings.py:13, portanto esta é a única ocorrência remanescente do literal no projeto, confirmada por varredura no escopo de código-fonte.
Impact: O literal está no histórico de versionamento e não pode ser rotacionado sem alterar o código. É o caso de correção parcial que a varredura de resíduo existe para detectar: a atribuição foi corrigida e a cópia na resposta permaneceu.
Recommendation: Remover o literal junto com a chave da resposta, conforme F04. Aplicar T2, categoria B, com a varredura de resíduo.

### [CRITICAL] Senha devolvida na resposta da API (F06, C6) [contract-breaking]
File: src/models/usuario_model.py:3-9
Locations: src/models/usuario_model.py:3-9, src/models/usuario_model.py:12-15, src/models/usuario_model.py:18-21
Description: A tupla `CAMPOS` inclui `senha`, e `_to_dict` devolve todos os campos. Os dois consumidores, `get_all` e `get_by_id`, alimentam `GET /usuarios` e `GET /usuarios/<id>`. O comentário nas linhas 7 e 8 registra que a correção foi recusada no portão da execução anterior.
Impact: Cliente sem autenticação obtém a senha de qualquer usuário por `GET /usuarios`. Combinado com F01, a senha vem em texto puro e é utilizável de imediato.
Recommendation: Remover o campo da serialização pública e usar serialização própria onde a credencial for necessária. Aplicar T18.
Contract change: `GET /usuarios` e `GET /usuarios/<id>` deixam de devolver a chave `senha`. As demais chaves permanecem inalteradas.

### [HIGH] Política de origem cruzada aberta (F07, H8) [contract-breaking]
File: src/config/settings.py:8
Locations: src/config/settings.py:8, src/app.py:16
Description: `CORS_ORIGINS` tem `*` como valor padrão, e `src/app.py:16` passa a lista a `CORS(app, origins=...)`. Sem variável de ambiente definida, o cabeçalho de resposta libera qualquer origem.
Impact: Qualquer origem pode emitir requisição contra a API pelo navegador do usuário. Combinado com F02 e F03, uma página de terceiro dispara `POST /admin/reset-db` e `POST /admin/query`.
Recommendation: Manter a lista configurável com o padrão aberto preserva o comportamento atual e encerra a constatação como MITIGADA, não como CORRIGIDA. Adotar lista restritiva como padrão fecha de fato. Aplicar T19.
Contract change: Somente se a lista restritiva for autorizada. O cabeçalho `Access-Control-Allow-Origin` deixa de ser `*` para toda resposta dos 19 endpoints.

### [HIGH] Corpo do erro 500 devolve o texto da exceção (F08, C6) [contract-breaking]
File: src/middlewares/error_handler.py:9-15
Description: O tratador central termina em `return jsonify({"erro": str(exc)}), 500`. Com o driver de banco, `str(exc)` inclui o comando SQL completo e a lista de colunas da tabela envolvida. O corpo reproduz o que os blocos `try` do código original produziam, confirmado em 6d1ce62, portanto é preservação fiel e não defeito introduzido pela refatoração anterior.
Impact: Uma falha interna entrega ao cliente anônimo o texto da consulta e o nome das colunas, inclusive `senha`. O detalhe já é registrado por `logger.exception` na linha 14, que é o destino adequado.
Recommendation: Substituir por mensagem fixa, mantendo o detalhe apenas no registro de log. Aplicar T11.
Contract change: O corpo de toda resposta 500 deixa de conter o texto da exceção e passa a conter uma mensagem fixa. O código de status não muda.

### [MEDIUM] Camada de configuração contém esquema e acesso a dados (F09, MVC)
File: src/config/database.py:26-84
Description: `init_db` executa quatro comandos `CREATE TABLE`, uma consulta `SELECT COUNT(*)` e dois `INSERT` de carga inicial. A tabela `contém / não contém` atribui a `config/` a leitura de ambiente e constantes nomeadas, e exclui consulta.
Impact: Alterar o esquema do banco exige editar a camada de configuração. A carga inicial, que é dado de domínio, fica no mesmo arquivo que o caminho do banco, o que é a origem de F01 estar em `config/`.
Recommendation: Mover a criação de esquema e a carga inicial para a camada de modelo, mantendo em `config/` apenas o caminho do banco e a fábrica de conexão. Aplicar T3.

### [MEDIUM] Corpo da requisição lido sem guarda (F10, M3) [contract-breaking]
File: src/controllers/admin_controller.py:17-18
Locations: src/controllers/admin_controller.py:17-18, src/controllers/pedido_controller.py:53-54, src/controllers/usuario_controller.py:41-43
Description: Três handlers leem o corpo e chamam `.get` diretamente, sem a verificação `if not dados` que os outros quatro aplicam. Corpo JSON nulo produz `AttributeError`, e corpo JSON válido que não seja objeto, como `"abc"`, produz o mesmo erro nos sete handlers de escrita, porque `if not dados` aprova qualquer valor verdadeiro.
Impact: Erro de cliente produz 500 em vez de 400, e o corpo do 500 expõe o texto da exceção por F08. A mesma classe de entrada recebe tratamento diferente conforme o endpoint.
Recommendation: Verificar em ponto único que o corpo é objeto, e consumir essa verificação nos sete handlers de escrita. Aplicar T20.
Contract change: `POST /admin/query`, `PUT /pedidos/<id>/status`, `POST /login`, `POST /produtos`, `PUT /produtos/<id>`, `POST /usuarios` e `POST /pedidos` passam a devolver 400 para corpo nulo e para corpo JSON que não seja objeto, hoje respondidos com 500.

### [MEDIUM] Atualização de status não verifica se o pedido existe (F11, M3) [contract-breaking]
File: src/controllers/pedido_controller.py:52-66
Description: `atualizar_status` valida o valor do status e chama `pedido_model.update_status`, que executa `UPDATE pedidos SET status = ? WHERE id = ?` sem verificar o resultado. Um identificador inexistente atualiza zero linhas e o handler devolve 200 com a mensagem de sucesso.
Impact: O cliente recebe confirmação de uma escrita que não ocorreu. Os demais handlers do projeto verificam a existência antes de escrever, conforme `produto_controller.atualizar` em src/controllers/produto_controller.py:61-63.
Recommendation: Verificar a existência do pedido antes da escrita, como a rota de produto já faz. Aplicar T20.
Contract change: `PUT /pedidos/<id>/status` passa a devolver 404 para identificador inexistente, hoje respondido com 200.

### [MEDIUM] Bloco de validação duplicado entre criar e atualizar (F12, M2)
File: src/controllers/produto_controller.py:26-48,65-83
Description: As verificações de corpo obrigatório, campos obrigatórios, preço não negativo e estoque não negativo aparecem duas vezes no mesmo arquivo, com as mesmas mensagens. A verificação de tamanho de nome e de categoria válida existe apenas em `criar`, nas linhas 45 a 51, e não em `atualizar`.
Impact: Uma correção na validação precisa ser aplicada nos dois pontos. A divergência já existe: `PUT /produtos/<id>` aceita nome de um caractere e categoria fora da lista, entrada que `POST /produtos` recusa.
Recommendation: Extrair a sequência de verificações para função única consumida pelos dois handlers. Aplicar T10.

### [MEDIUM] Validação sem verificação de tipo em produto (F13, M3) [contract-breaking]
File: src/controllers/produto_controller.py:41-44,80-83,105-108
Description: `preco < 0` e `estoque < 0` comparam sem verificar o tipo recebido, e `float(preco_min)` converte argumento de consulta sem bloco protegido. Um preço textual produz `TypeError` na comparação, e `?preco_min=abc` produz `ValueError`.
Impact: `POST /produtos` com `{"nome":"X","preco":"caro","estoque":1}` devolve 500 em vez de 400, e `GET /produtos/busca?preco_min=abc` devolve 500. O corpo do 500 expõe o texto da exceção por F08.
Recommendation: Verificar o tipo antes de comparar e converter o argumento de consulta dentro de bloco protegido. Aplicar T20.
Contract change: `POST /produtos`, `PUT /produtos/<id>` e `GET /produtos/busca` passam a devolver 400 para preço, estoque ou faixa de preço de tipo inválido, hoje respondidos com 500.

### [LOW] Envelope de resposta inconsistente (F14, L4) [contract-breaking]
File: src/controllers/home_controller.py:4-16
Locations: src/controllers/home_controller.py:4-16, src/controllers/produto_controller.py:86,96, src/controllers/relatorio_controller.py:12-25
Description: Dezesseis endpoints devolvem o envelope `{"dados": ..., "sucesso": true}`. `GET /` e `GET /health` devolvem objeto sem envelope, com chaves próprias. `PUT /produtos/<id>` e `DELETE /produtos/<id>` devolvem `{"sucesso": ..., "mensagem": ...}` sem a chave `dados`.
Impact: O cliente precisa de tratamento por endpoint em vez de tratamento único para ler o resultado.
Recommendation: A recomendação padrão é não aplicar. O ganho é de padronização e o custo é a quebra dos consumidores das rotas afetadas. Aplicar T22 apenas se autorizado.
Contract change: `GET /`, `GET /health`, `PUT /produtos/<id>` e `DELETE /produtos/<id>` passam a devolver o envelope `{"dados": ..., "sucesso": true}`, com o corpo atual movido para dentro da chave `dados`.

### [LOW] Literais de ambiente na resposta de saúde (F15, L1)
File: src/controllers/relatorio_controller.py:17-19
Description: As chaves `versao`, `ambiente` e `db_path` recebem os literais `1.0.0`, `producao` e `loja.db`, escritos no handler. O caminho do banco já existe como `DB_PATH` em src/config/settings.py:5, e o valor devolvido não acompanha a variável de ambiente.
Impact: O endpoint informa `loja.db` mesmo quando `DB_PATH` aponta para outro arquivo, e informa `producao` em qualquer ambiente. A informação devolvida não corresponde ao estado da aplicação.
Recommendation: Extrair para constantes nomeadas no módulo de configuração e derivar o caminho do banco de `DB_PATH`, preservando os valores atuais como padrão. Aplicar T13.

================================
Total: 15 findings
================================
