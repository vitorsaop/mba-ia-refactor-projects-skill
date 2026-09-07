================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 10 | HIGH: 6 | MEDIUM: 7 | LOW: 6

## Findings

### [CRITICAL] Chave secreta embutida no código (C2)
File: app.py:7
Description: `app.config["SECRET_KEY"]` recebe o literal `"minha-chave-super-secreta-123"` diretamente no código. O mesmo valor é devolvido pelo endpoint `/health` em controllers.py:289.
Impact: A chave entra no histórico de versionamento e não pode ser rotacionada sem editar e reimplantar o código.
Recommendation: Ler de variável de ambiente, com o literal atual como padrão apenas se a variável estiver ausente. Aplicar T2, categoria segredo.

### [CRITICAL] Módulo com múltiplas responsabilidades (C7)
File: app.py:7-9,11-30,47-78
Description: O mesmo arquivo concentra configuração (linhas 7-9: SECRET_KEY, DEBUG, CORS), roteamento (linhas 11-30: 16 chamadas a `add_url_rule`) e acesso direto a banco com regra administrativa (linhas 47-78: `reset_database` e `executar_query` executam SQL diretamente no handler de rota).
Impact: Uma mudança em qualquer uma das três responsabilidades exige tocar no mesmo arquivo, e nenhuma pode ser testada isoladamente.
Recommendation: Separar em `config/`, `routes/` e mover a lógica administrativa para controller e model próprios. Aplicar T3, T15.

### [CRITICAL] Modo de depuração ativo (C8)
File: app.py:8,88
Description: `app.config["DEBUG"] = True` (linha 8) e `app.run(..., debug=True)` (linha 88) ativam o modo de depuração sem condicionamento a variável de ambiente.
Impact: O console interativo de execução do Werkzeug fica acessível e o rastreamento completo de exceção é exposto ao cliente em qualquer erro não tratado.
Recommendation: Condicionar `debug` a uma variável de ambiente (`DEBUG=false` como padrão). Aplicar T2.

### [CRITICAL] Operação destrutiva sem autenticação (C4) [contract-breaking]
File: app.py:47-57
Description: `POST /admin/reset-db` executa `DELETE FROM` nas quatro tabelas (itens_pedido, pedidos, produtos, usuarios) sem qualquer verificação de identidade ou permissão no caminho de execução.
Impact: Qualquer cliente com acesso de rede ao endpoint apaga todos os dados da aplicação.
Recommendation: Exigir autenticação e autorização de administrador antes de executar a limpeza, ou remover o endpoint do código de produção. Aplicar T16.
Contract change: `POST /admin/reset-db` passa a exigir credencial de administrador; sem ela, devolve 401/403 em vez de 200.

### [CRITICAL] Endpoint que executa comando SQL arbitrário (C3) [contract-breaking]
File: app.py:59-78
Description: `POST /admin/query` recebe a chave `sql` do corpo da requisição e a repassa diretamente para `cursor.execute(query)`, sem qualquer filtro.
Impact: Concede a qualquer cliente a capacidade total da conta de banco: leitura, alteração e remoção de qualquer tabela.
Recommendation: Remover o endpoint da aplicação exposta publicamente. Aplicar T16.
Contract change: `POST /admin/query` deixa de existir.

### [CRITICAL] Chave secreta e modo debug na resposta de /health (C6) [contract-breaking]
File: controllers.py:285-289
Description: O corpo devolvido por `GET /health` inclui as chaves `debug` (linha 288) e `secret_key` (linha 289) com valores reais de configuração da aplicação.
Impact: Qualquer cliente com acesso ao endpoint de health check obtém a chave de configuração e o estado do modo debug sem autenticação.
Recommendation: Remover as chaves `debug` e `secret_key` do corpo de resposta. Aplicar T18.
Contract change: `GET /health` deixa de devolver as chaves `debug` e `secret_key`. As demais chaves (`status`, `database`, `counts`, `versao`, `ambiente`, `db_path`) permanecem inalteradas.

### [CRITICAL] Senha em texto puro nos dados de seed (C5) [contract-breaking]
File: database.py:75-83
Description: Os três usuários de exemplo são inseridos com senha literal em texto puro (`admin123`, `123456`, `senha123`) na coluna `senha`.
Impact: Qualquer leitura da tabela `usuarios`, incluindo pelos próprios endpoints da API, expõe a senha original sem necessidade de quebrar hash algum.
Recommendation: Persistir hash da senha com sal, gerado a partir do mesmo valor de seed. Aplicar T17.
Contract change: O valor persistido na coluna `senha` deixa de ser igual ao texto original; comparações futuras exigem verificação de hash em vez de igualdade direta.

### [CRITICAL] SQL Injection por concatenação (C1)
File: models.py:28,47-50,57-61,68,92,109-111,126-129,140,148-151,155,157-161,163-166,174,188,192,220,224,279-297
Description: Praticamente toda consulta do módulo é montada por concatenação de string com valor vindo da requisição, incluindo `get_produto_por_id` (28), `criar_produto` (47-50), `atualizar_produto` (57-61), `deletar_produto` (68), `get_usuario_por_id` (92), `login_usuario` (109-111, email e senha do corpo da requisição diretamente na cláusula WHERE), `criar_usuario` (126-129), `criar_pedido` (140,148-151,155,157-161,163-166), `get_pedidos_usuario` (174,188,192), `get_todos_pedidos` (220,224), `atualizar_status_pedido` (279-281) e `buscar_produtos` (289-297, filtro montado por concatenação incremental).
Impact: Um cliente pode alterar a estrutura de qualquer uma dessas consultas e ler, alterar ou remover registros fora do escopo do endpoint. Em `login_usuario`, a autenticação pode ser contornada com uma condição sempre verdadeira.
Recommendation: Substituir todas as ocorrências por consulta parametrizada com marcador `?`. Aplicar T1.

### [CRITICAL] Senha exposta na resposta da API (C6) [contract-breaking]
File: models.py:79-86,95-102
Description: `get_todos_usuarios` (79-86) e `get_usuario_por_id` (95-102) incluem a chave `senha` com o valor bruto do banco no dicionário devolvido, que é repassado sem filtro por `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Qualquer cliente que liste ou busque um usuário recebe a senha em texto puro, sem necessidade de acesso ao banco.
Recommendation: Criar uma representação pública sem o campo `senha`, e usar uma representação separada apenas no caminho de autenticação. Aplicar T18 (equivalente a ISP, ver `solid-principles.md`).
Contract change: `GET /usuarios` e `GET /usuarios/<id>` deixam de devolver a chave `senha`. As demais chaves permanecem inalteradas.

### [CRITICAL] Senha comparada e armazenada sem hash (C5) [contract-breaking]
File: models.py:109-111,126-129
Description: `login_usuario` (109-111) compara a senha por igualdade direta dentro da própria consulta SQL, e `criar_usuario` (126-129) insere a senha recebida sem qualquer transformação.
Impact: A senha fica recuperável em texto puro por qualquer leitura da tabela, e a comparação direta impede a adoção de um algoritmo de hash sem alterar o formato de dado já persistido.
Recommendation: Persistir hash com sal em `criar_usuario` e comparar hash em `login_usuario`. Aplicar T17.
Contract change: Senhas já persistidas em texto puro precisam de migração para hash; o formato do dado armazenado muda.

### [HIGH] Política de origem cruzada aberta (H8)
File: app.py:9
Description: `CORS(app)` é chamado sem argumento de origem, liberando qualquer origem para requisições contra a API.
Impact: Qualquer site pode emitir requisições autenticadas pelo navegador contra os endpoints desta API.
Recommendation: Restringir `CORS` às origens confiáveis declaradas em configuração. Aplicar T19.

### [HIGH] Rotas administrativas sem camada de controller ou model (MVC)
File: app.py:47-78
Description: `reset_database` e `executar_query` são handlers de rota que chamam `get_db()` e executam SQL diretamente, sem passar por controller nem por model, violando a coluna "não contém" de `views/routes` e do ponto de entrada em `mvc-architecture.md`.
Impact: Não há ponto único de validação ou de montagem de resposta para essas duas rotas; qualquer alteração de fluxo exige editar o arquivo de composição da aplicação.
Recommendation: Mover a lógica para um controller e um model de administração dedicados. Aplicar T4, T5.

### [HIGH] Controller acessando o driver do banco diretamente (MVC)
File: controllers.py:264-292
Description: `health_check` importa `get_db` de `database` e executa `cursor.execute("SELECT 1")` e três contagens diretamente no controller, violando a coluna "não contém" de `controllers/` em `mvc-architecture.md` (SQL literal, acesso direto ao driver do banco).
Impact: A lógica de contagem não pode ser reutilizada nem testada fora do contexto HTTP, e duplica no controller uma responsabilidade que pertence ao model.
Recommendation: Mover as consultas para um model de health/relatório e fazer o controller apenas chamá-lo. Aplicar T4, T5.

### [HIGH] Estado global mutável na conexão de banco (H3 / DIP)
File: database.py:4,7-12
Description: A conexão é mantida na variável de módulo `db_connection`, reatribuída dentro de `get_db()` via `global`, com `check_same_thread=False`, e é a única fonte de dados usada por toda a aplicação (importada diretamente por `models.py`).
Impact: Requisições concorrentes compartilham a mesma conexão. Não é possível trocar a origem dos dados nem testar uma função de acesso a dados sem subir esse estado global.
Recommendation: Substituir por fábrica de conexão com escopo de requisição, recebida por parâmetro em vez de importada globalmente. Aplicar T6.

### [HIGH] Módulo cobre múltiplos domínios de negócio (SRP)
File: models.py:4-273
Description: Um único arquivo de 315 linhas concentra quatro domínios distintos: produto (4-70), usuário e autenticação (72-131), pedido e estoque (133-233) e relatório de vendas (235-273), cada um com sua própria razão para mudar.
Impact: Uma mudança na regra de desconto do relatório e uma mudança no cadastro de produto exigem editar o mesmo arquivo, aumentando o risco de uma alteração afetar um domínio não relacionado.
Recommendation: Dividir em `produto_model.py`, `usuario_model.py`, `pedido_model.py` e `relatorio_model.py`. Aplicar T3.

### [HIGH] Escrita em múltiplos passos sem transação (H6)
File: models.py:133-169
Description: `criar_pedido` insere o pedido (148-151), depois em laço insere cada item (157-161) e atualiza o estoque (163-166), com um único `commit()` ao final (168) e nenhum `rollback` no caminho de erro.
Impact: Uma falha após o insert do pedido e antes do commit final deixa o pedido sem itens ou com estoque debitado de forma inconsistente.
Recommendation: Envolver a sequência em um bloco transacional único com rollback no caminho de exceção. Aplicar T9.

### [MEDIUM] Tratamento de erro não centralizado (M4)
File: controllers.py:5,14,24,64,98,111,128,136,146,167,188,222,229,237,257,264
Description: Os 16 handlers do arquivo repetem o mesmo bloco `try / except Exception as e: return jsonify({"erro": str(e)}), 500`, e `app.py` não registra nenhum tratador de erro central no ponto de entrada.
Impact: O formato do erro depende de qual handler falhou, e adicionar um novo endpoint exige replicar o mesmo bloco novamente.
Recommendation: Registrar um tratador de erro central no ponto de entrada e remover o `try/except` repetido de cada handler. Aplicar T11.

### [MEDIUM] Validação de entrada incompleta (M3)
File: controllers.py:64-96,146-165
Description: `atualizar_produto` (64-96) não valida tamanho de `nome` nem pertencimento de `categoria` à lista de categorias válidas, embora `criar_produto` valide ambos. `criar_usuario` (146-165) não valida formato de email nem tamanho mínimo de senha.
Impact: Um produto pode ser atualizado com nome de um caractere ou categoria inexistente, e um usuário pode ser criado com email malformado ou senha vazia de um caractere.
Recommendation: Aplicar as mesmas verificações de `criar_produto` também em `atualizar_produto`, e validar formato de email e tamanho mínimo de senha em `criar_usuario`. Aplicar T20.

### [MEDIUM] Importação não utilizada (M5)
File: database.py:2
Description: O módulo `os` é importado e nunca referenciado no arquivo.
Impact: Sugere uma dependência de variável de ambiente que não existe, o que confunde a leitura do módulo.
Recommendation: Remover a importação não utilizada. Aplicar T12.

### [MEDIUM] Importação não utilizada (M5)
File: models.py:2
Description: O módulo `sqlite3` é importado e nunca referenciado diretamente no arquivo; todo acesso passa pelo objeto de conexão devolvido por `get_db()`.
Impact: Sugere uma dependência direta do driver que não existe de fato neste módulo.
Recommendation: Remover a importação não utilizada. Aplicar T12.

### [MEDIUM] Lógica duplicada (M2)
File: models.py:12-21,31-40,178-200,211-232,304-313
Description: A montagem do dicionário de produto (id, nome, descricao, preco, estoque, categoria, ativo, criado_em) é repetida de forma quase idêntica em `get_todos_produtos` (12-21), `get_produto_por_id` (31-40) e `buscar_produtos` (304-313). A montagem de pedido com itens aninhados é repetida quase idêntica em `get_pedidos_usuario` (178-200) e `get_todos_pedidos` (211-232).
Impact: Uma mudança no formato de saída do produto ou do pedido precisa ser replicada em até três pontos; um ponto esquecido produz resposta divergente entre endpoints.
Recommendation: Extrair cada montagem para uma função única reaproveitada pelos três (ou dois) pontos de chamada. Aplicar T10.

### [MEDIUM] Consulta dentro de laço (M1)
File: models.py:140,155,188,192,220,224
Description: `criar_pedido` consulta o produto uma vez por item dentro do laço de validação (140) e novamente dentro do laço de inserção (155). `get_pedidos_usuario` (188,192) e `get_todos_pedidos` (220,224) abrem um cursor por pedido e outro por item dentro dele.
Impact: Um relatório com N pedidos e M itens por pedido executa 1 + N + N×M consultas; o tempo de resposta cresce com o volume de dados.
Recommendation: Substituir por consulta única com JOIN entre pedidos, itens_pedido e produtos, e eliminar a segunda consulta redundante em `criar_pedido`. Aplicar T7.

### [MEDIUM] Cadeia condicional para faixa de desconto (OCP)
File: models.py:256-262
Description: `relatorio_vendas` decide a taxa de desconto por uma cadeia `if/elif` sobre o faturamento, com um ramo por faixa.
Impact: Acrescentar uma nova faixa de desconto exige editar esta função e reordenar as comparações existentes.
Recommendation: Extrair as faixas para uma lista ordenada de configuração e percorrê-la em vez de comparar em cadeia, preservando os mesmos limites e taxas. Aplicar T13.

### [LOW] Saída em terminal como registro de log (L3)
File: app.py:56,83-86
Description: `print("!!! BANCO DE DADOS RESETADO !!!")` (56) e o banner de inicialização (83-86) usam `print` em vez de um registro de log com nível.
Impact: Não há como filtrar por severidade nem direcionar a saída para um coletor de log em produção.
Recommendation: Substituir por chamada de log com nível apropriado. Aplicar T23.

### [LOW] Saída em terminal como registro de log (L3)
File: controllers.py:8,11,57,61,106,161,179,182,208-210,219,248,250
Description: Catorze chamadas a `print` espalhadas pelos handlers registram operação, erro e simulação de notificação (`ENVIANDO EMAIL`, `ENVIANDO SMS`, `ENVIANDO PUSH`, `NOTIFICAÇÃO`) em vez de log com nível.
Impact: Não há como filtrar por severidade nem suprimir a saída por configuração em produção.
Recommendation: Substituir por chamadas de log com nível apropriado (info para operação, error para exceção). Aplicar T23.

### [LOW] Nome sem significado (L2)
File: controllers.py:14,64,98,136
Description: Os parâmetros `id` de `buscar_produto`, `atualizar_produto`, `deletar_produto` e `buscar_usuario` sombreiam o built-in `id` da linguagem.
Impact: Qualquer uso de `id()` embutido dentro dessas funções resolveria para o parâmetro, não para a função embutida.
Recommendation: Renomear para um nome específico do domínio, como `produto_id` ou `usuario_id`. Aplicar T21.

### [LOW] Formato de resposta inconsistente (L4)
File: controllers.py:20,142
Description: O erro 404 de `buscar_produto` (20) inclui a chave `sucesso: False`, enquanto o erro 404 de `buscar_usuario` (142) só devolve `erro`, sem a chave `sucesso`.
Impact: O cliente precisa tratar o formato de erro de forma diferente para cada endpoint em vez de um único tratamento genérico.
Recommendation: Padronizar o envelope de erro para incluir sempre `erro` e `sucesso: False`. Aplicar T22.

### [LOW] Número mágico (L1)
File: controllers.py:47,49
Description: Os limites `2` e `200` para o tamanho do campo `nome` aparecem como literais na comparação, sem nome.
Impact: O significado dos limites não é recuperável pela leitura, e a alteração exige localizar a comparação no meio da função.
Recommendation: Extrair para constantes nomeadas (`NOME_MIN_LENGTH`, `NOME_MAX_LENGTH`), preservando os mesmos valores. Aplicar T13.

### [LOW] Nome sem significado (L2)
File: models.py:24,54,65,89
Description: Os parâmetros `id` de `get_produto_por_id`, `atualizar_produto`, `deletar_produto` e `get_usuario_por_id` sombreiam o built-in `id` da linguagem.
Impact: Qualquer uso de `id()` embutido dentro dessas funções resolveria para o parâmetro, não para a função embutida.
Recommendation: Renomear para um nome específico do domínio, como `produto_id` ou `usuario_id`. Aplicar T21.

================================
Total: 29 findings
================================
