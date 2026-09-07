================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 9 | HIGH: 11 | MEDIUM: 20 | LOW: 13

## Findings

### [CRITICAL] Chave secreta embutida no código (F01, C2)
File: app.py:13
Description: `app.config['SECRET_KEY']` recebe o literal `'super-secret-key-123'`. A busca por `session`, `flash`, `set_cookie` e `itsdangerous` no projeto não devolve nenhuma ocorrência, portanto a chave não assina nada hoje.
Impact: O literal está no histórico de versionamento e não pode ser rotacionado sem alterar o código. Qualquer pessoa com acesso ao repositório obtém a chave.
Recommendation: Remover o literal e ler de variável de ambiente. Como a chave não assina nada, gerar por boot quando a variável estiver ausente. Aplicar T2, categoria B.

### [CRITICAL] Modo de depuração ativo no boot (F02, C8)
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` fixa `debug=True` como literal, sem condicionamento a variável de ambiente.
Impact: O console interativo do Werkzeug fica acessível e qualquer exceção não tratada devolve o rastreamento completo ao cliente. O bind em `0.0.0.0` expõe esse console à rede.
Recommendation: Mover `debug`, `host` e `port` para o módulo de configuração, com `DEBUG` lido do ambiente e padrão desligado. Aplicar T2, categoria A.

### [CRITICAL] Hash de senha devolvido na resposta da API (F03, C6) [contract-breaking]
File: models/user.py:16-25
Locations: models/user.py:21, routes/user_routes.py:33, routes/user_routes.py:85-86, routes/user_routes.py:129, routes/user_routes.py:209
Description: `User.to_dict()` inclui a chave `password` com o digest armazenado. Quatro endpoints consomem essa serialização: `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. A serialização única atende consumidores que não precisam do campo, o que é também violação de ISP com dado sensível.
Impact: Qualquer cliente sem autenticação obtém o digest MD5 de qualquer usuário por `GET /users/<id>`. Combinado com F04, o digest é reversível por tabela pré-computada.
Recommendation: Substituir `to_dict` por serialização sem o campo de senha e usar uma serialização própria onde a credencial é de fato necessária. Aplicar T18.
Contract change: `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` deixam de devolver a chave `password`. Em `POST /login` a chave sai de dentro do objeto `user`. As demais chaves permanecem inalteradas.

### [CRITICAL] Senha armazenada com MD5 sem sal (F04, C5) [contract-breaking]
File: models/user.py:27-32
Description: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara o digest por igualdade direta. Não há sal nem fator de custo.
Impact: MD5 é rápido e sem sal, portanto os digests são recuperáveis por tabela pré-computada. Senhas iguais produzem digests iguais, o que revela reuso de senha entre usuários. A comparação por igualdade direta não é de tempo constante.
Recommendation: Substituir por `hashlib.pbkdf2_hmac` com sal por usuário e comparação com `hmac.compare_digest`, ambos da biblioteca padrão. Aplicar T17.
Contract change: Os digests já persistidos deixam de validar. `POST /login` passa a devolver 401 para as credenciais gravadas por `seed.py` até que o script de carga inicial seja executado novamente. O formato do valor armazenado muda de 32 caracteres hexadecimais para `pbkdf2_sha256$<iteracoes>$<sal>$<digest>`.

### [CRITICAL] Arquivo de rotas concentra dados, regra e roteamento (F05, C7)
File: routes/report_routes.py:1-223
Description: O arquivo reúne quatro responsabilidades: definição de 6 rotas (linhas 12, 103, 157, 167, 190, 211), acesso a dados por ORM (32 chamadas a `Task.query`, `User.query` e `Category.query`), regra de negócio (agregação em 30-68 e 119-135, taxa de conclusão em 67 e 151) e formatação de saída (montagem dos dicionários em 70-99 e 137-153). Cobre também dois domínios distintos, relatórios e categorias, o que é violação de SRP em duas dimensões.
Impact: Uma mudança na fórmula de produtividade e uma mudança no cadastro de categorias obrigam a editar o mesmo arquivo. Nenhuma das duas regras pode ser exercitada sem construir uma requisição HTTP.
Recommendation: Separar por domínio em `models/`, `controllers/` e `views/`, movendo as funções sem alterar o corpo. Aplicar T3 e T15.

### [CRITICAL] Arquivo de rotas concentra dados, regra e roteamento (F06, C7)
File: routes/task_routes.py:1-299
Description: O arquivo reúne quatro responsabilidades: definição de 7 rotas (linhas 11, 65, 85, 156, 225, 240, 273), acesso a dados por ORM (19 chamadas a `Task.query`, `User.query` e `Category.query`), regra de negócio (cálculo de atraso em 30-39, 71-80 e 283-287, taxa de conclusão em 296) e formatação de saída (montagem manual do dicionário em 17-28).
Impact: Uma mudança na regra de atraso e uma mudança no formato de resposta obrigam a editar o mesmo arquivo. A regra de atraso não pode ser exercitada sem construir uma requisição HTTP.
Recommendation: Separar em `models/`, `controllers/` e `views/`, movendo as funções sem alterar o corpo. Aplicar T3 e T15.

### [CRITICAL] Arquivo de rotas concentra dados, regra e roteamento (F07, C7)
File: routes/user_routes.py:1-211
Description: O arquivo reúne quatro responsabilidades: definição de 7 rotas (linhas 10, 27, 42, 92, 134, 153, 185), acesso a dados por ORM (12 chamadas a `User.query` e `Task.query`), regra de negócio (validação de formato de email em 61 e 106, autenticação em 197-211, remoção em cascata em 140-142) e formatação de saída (montagem manual dos dicionários em 15-23 e 162-169).
Impact: Uma mudança na política de senha e uma mudança na listagem de tarefas do usuário obrigam a editar o mesmo arquivo. A regra de autenticação não pode ser exercitada sem construir uma requisição HTTP.
Recommendation: Separar em `models/`, `controllers/` e `views/`, movendo as funções sem alterar o corpo. Aplicar T3 e T15.

### [CRITICAL] Operações destrutivas sem autenticação (F08, C4) [contract-breaking]
File: routes/user_routes.py:134-151
Locations: routes/report_routes.py:211-223, routes/task_routes.py:225-238, routes/user_routes.py:134-151
Description: Três endpoints removem registros sem nenhuma verificação de identidade ou permissão no caminho de execução: `DELETE /users/<id>`, que também remove em massa todas as tarefas do usuário nas linhas 140-142, `DELETE /tasks/<id>` e `DELETE /categories/<id>`. O projeto define `User.is_admin()` em models/user.py:34-38 e nunca o chama. O `token` devolvido por `POST /login` em routes/user_routes.py:210 é a concatenação `'fake-jwt-token-' + str(user.id)` e não é verificado em nenhum endpoint.
Impact: Qualquer cliente com acesso de rede apaga qualquer usuário, tarefa ou categoria. Uma requisição a `DELETE /users/1` remove o usuário e todas as tarefas associadas a ele.
Recommendation: Proteger os três endpoints com verificação de credencial administrativa em middleware, preservando a função. Aplicar T16, opção B.
Contract change: `DELETE /users/<id>`, `DELETE /tasks/<id>` e `DELETE /categories/<id>` passam a devolver 401 com corpo `{"error": "Não autorizado"}` para requisição sem o cabeçalho de credencial. Com credencial válida, corpo e status permanecem idênticos.

### [CRITICAL] Credenciais de SMTP embutidas no código (F09, C2)
File: services/notification_service.py:7-10
Description: O construtor atribui os literais `'smtp.gmail.com'`, `587`, `'taskmanager@gmail.com'` e `'senha123'` a `email_host`, `email_port`, `email_user` e `email_password`. O literal de senha é consumido em `server.login(self.email_user, self.email_password)` na linha 17.
Impact: A senha do remetente está no histórico de versionamento e não pode ser rotacionada sem alterar o código. Quem obtiver o repositório envia email pela conta.
Recommendation: O único consumidor deste segredo é código morto: a classe `NotificationService` não é importada em nenhum arquivo do projeto, conforme F39. O segredo é da categoria C e sai junto com o módulo. Aplicar T2, categoria C, e T12.

### [HIGH] Política de origem cruzada aberta (F10, H8) [contract-breaking]
File: app.py:15
Description: `CORS(app)` é chamado sem argumento de origem, o que produz o cabeçalho `Access-Control-Allow-Origin: *` em todas as respostas.
Impact: Qualquer origem passa a poder emitir requisições contra a API pelo navegador do usuário. Combinado com F08, uma página de terceiro dispara `DELETE /users/<id>`.
Recommendation: Extrair a lista de origens para o módulo de configuração, com o valor aberto como padrão para preservar o comportamento atual. Aplicar T19. O padrão aberto encerra a constatação como MITIGADA, não como CORRIGIDA. Adotar lista restritiva como padrão fecha de fato e altera o contrato.
Contract change: Somente se a lista restritiva for autorizada. O cabeçalho `Access-Control-Allow-Origin` deixa de ser `*` e passa a refletir apenas as origens declaradas, para toda resposta de todos os 22 endpoints.

### [HIGH] Camada de controller inexistente (F11, H2)
File: routes/report_routes.py:2-5
Locations: routes/report_routes.py:2-5, routes/task_routes.py:2-5, routes/user_routes.py:2-4
Description: Os três arquivos de rota importam `db` e os modelos diretamente e executam persistência dentro do próprio handler de rota. Não existe diretório `controllers/` no projeto.
Impact: O fluxo de cada requisição está preso à definição da rota. Não há ponto único para validação de entrada nem para montagem de resposta, e cada handler repete as duas coisas.
Recommendation: Criar a camada de controllers, mover cada handler para o controller do seu domínio e reduzir os arquivos de rota a associações entre caminho, método e controller. Aplicar T4 e T5.

### [HIGH] Contagem por valor de domínio com um ramo por caso (F12, OCP)
File: routes/report_routes.py:19-28,119-127
Locations: routes/report_routes.py:19-28, routes/report_routes.py:119-127, routes/task_routes.py:275-279
Description: A contagem por status é escrita como uma consulta por valor em routes/report_routes.py:19-22 e em routes/task_routes.py:275-279, e como cadeia `if/elif` com um ramo por valor em routes/report_routes.py:119-127. A contagem por prioridade é escrita como cinco consultas nomeadas `p1` a `p5` em routes/report_routes.py:24-28.
Impact: Acrescentar um status exige editar três blocos em dois arquivos de forma sincronizada. Um bloco esquecido produz contagem divergente entre `GET /tasks/stats` e `GET /reports/summary`.
Recommendation: Extrair a lista de status e de prioridades para constante nomeada no módulo de configuração e derivar as contagens por agregação sobre essa lista, preservando as mesmas chaves de resposta. Aplicar T13.

### [HIGH] Regra de negócio dentro dos handlers de relatório (F13, H1)
File: routes/report_routes.py:33-43,55-68,129-135
Description: O handler `summary_report` calcula o atraso e os dias de atraso em 33-43 e agrega produtividade por usuário em 55-68. O handler `user_report` classifica status por cadeia condicional, deriva prioridade alta com `t.priority <= 2` e recalcula o atraso em 119-135. A taxa de conclusão é calculada em 67 e 151.
Impact: As regras de atraso, de prioridade alta e de taxa de conclusão só podem ser exercitadas construindo uma requisição HTTP. A mesma regra de atraso existe em outros quatro pontos do projeto, conforme F26.
Recommendation: Mover os cálculos para a camada de modelo, reusando `Task.is_overdue()`, que já existe. Aplicar T5.

### [HIGH] Exceção capturada e descartada nos handlers de categoria (F14, H7)
File: routes/report_routes.py:186-188,207-209,221-223
Description: Três blocos usam `except:` sem tipo, executam `db.session.rollback()` e devolvem uma mensagem genérica sem registrar a causa: `'Erro ao criar categoria'`, `'Erro ao atualizar'` e `'Erro ao deletar'`.
Impact: A causa raiz da falha não é registrada em lugar algum. O diagnóstico em produção fica limitado ao código 500 e ao texto genérico. `except:` sem tipo captura também `KeyboardInterrupt` e `SystemExit`.
Recommendation: Remover os blocos e deixar a exceção subir para um tratador central registrado no ponto de entrada, com a guarda `isinstance(exc, HTTPException)`. Aplicar T11.

### [HIGH] Regra de negócio dentro dos handlers de task (F15, H1)
File: routes/task_routes.py:30-39,71-80,283-296
Description: O cálculo de atraso é escrito por extenso em 30-39, 71-80 e 283-287. A taxa de conclusão é calculada em 296. O handler `task_stats` carrega todas as tarefas em 281 e conta o atraso em laço em 283-287.
Impact: As regras de atraso e de taxa de conclusão só podem ser exercitadas construindo uma requisição HTTP. O método `Task.is_overdue()` implementa exatamente a mesma regra e não é chamado.
Recommendation: Mover os cálculos para a camada de modelo, reusando `Task.is_overdue()`. Aplicar T5.

### [HIGH] Exceção capturada e descartada nos handlers de task (F16, H7)
File: routes/task_routes.py:62-63,137-138,151-154,204-205,221-223,236-238
Description: As linhas 62, 137, 204 e 236 usam `except:` sem tipo. As linhas 151-154 e 221-223 usam `except Exception as e`; em 221-223 a variável `e` é ligada e nunca usada, e em 151-154 a causa vai para `print` em vez de registro com nível. O bloco de 62-63 envolve o handler `get_tasks` inteiro e converte qualquer falha em `{'error': 'Erro interno'}` com status 500.
Impact: A causa raiz da falha não é registrada de forma filtrável. O bloco de 62-63 esconde qualquer defeito na montagem da lista de tarefas atrás de uma mensagem genérica. `except:` sem tipo captura também `KeyboardInterrupt` e `SystemExit`.
Recommendation: Remover os blocos genéricos e deixar a exceção subir para um tratador central registrado no ponto de entrada, com a guarda `isinstance(exc, HTTPException)`. Onde o bloco existe para converter erro em código específico, nomear o tipo da exceção. Aplicar T11.

### [HIGH] Exceção capturada e descartada nos handlers de usuário (F17, H7)
File: routes/user_routes.py:87-90,130-132,149-151
Description: As linhas 130 e 149 usam `except:` sem tipo. As linhas 87-90 usam `except Exception as e` e enviam a causa para `print(f"ERRO: {str(e)}")`, sem nível e sem destino configurável.
Impact: A causa raiz da falha não é registrada de forma filtrável. `except:` sem tipo captura também `KeyboardInterrupt` e `SystemExit`.
Recommendation: Remover os blocos e deixar a exceção subir para um tratador central registrado no ponto de entrada, com a guarda `isinstance(exc, HTTPException)`. Aplicar T11.

### [HIGH] Regra de negócio dentro dos handlers de usuário (F18, H1)
File: routes/user_routes.py:140-142,171-180
Description: O handler `delete_user` implementa a remoção em cascata em 140-142, carregando as tarefas do usuário e marcando cada uma para remoção. O modelo `Task` declara o relacionamento em models/task.py:20 sem configuração de cascata, portanto a regra existe apenas no handler. O handler `get_user_tasks` recalcula o atraso em 171-180.
Impact: A regra de cascata só existe neste handler. Qualquer outro caminho que remova um usuário deixa tarefas órfãs apontando para um identificador inexistente. A regra de atraso não pode ser exercitada sem construir uma requisição HTTP.
Recommendation: Mover a cascata para a camada de modelo, como operação de domínio, e reusar `Task.is_overdue()` no cálculo de atraso. Aplicar T5.

### [HIGH] Acoplamento direto ao cliente de email (F19, H4)
File: services/notification_service.py:5-19
Description: O construtor fixa a configuração do servidor de email em atributos de instância nas linhas 6-10 e o método `send_email` instancia `smtplib.SMTP(self.email_host, self.email_port)` na linha 15. O construtor também inicializa `self.notifications = []` na linha 6, acumulador lido em `get_notifications` na linha 45 e alimentado em 31-36 sem limite nem política de expiração.
Impact: A regra de notificação não pode ser exercitada sem abrir uma conexão SMTP real. A origem do transporte não pode ser trocada sem editar a classe. A classe reúne transporte, regra e consulta de registro no mesmo tipo, o que obriga quem só consulta notificações a carregar a credencial de email.
Recommendation: Receber o transporte por parâmetro em vez de instanciá-lo, e separar transporte, registro e regra em tipos distintos. Aplicar T6. Como o módulo é código morto, conforme F39, a remoção prevista por T12 encerra esta constatação.

### [HIGH] Exceção capturada e descartada no módulo de apoio (F20, H7)
File: utils/helpers.py:44-50,88-89
Description: `parse_date` usa `except:` sem tipo em dois níveis aninhados nas linhas 46 e 49 e devolve `None` em qualquer falha. `process_task_data` usa `except:` sem tipo na linha 88 para converter falha de `int()` em mensagem de prioridade inválida.
Impact: A causa raiz da falha de conversão não é registrada. Um `None` devolvido por `parse_date` não distingue entrada com formato desconhecido de entrada de tipo errado. `except:` sem tipo captura também `KeyboardInterrupt` e `SystemExit`.
Recommendation: Nomear o tipo da exceção capturada, `ValueError` e `TypeError`, nos três blocos. Aplicar T11.

### [MEDIUM] Importações não utilizadas no ponto de entrada (F21, M5)
File: app.py:7
Description: `import os, sys, json, datetime` traz quatro símbolos. A busca no arquivo confirma que apenas `datetime` é referenciado, na linha 24.
Impact: A linha sugere dependências de sistema operacional e de serialização que o arquivo não tem, o que aumenta a superfície de leitura.
Recommendation: Reduzir a linha a `import datetime`. Aplicar T12.

### [MEDIUM] Tratamento de erro não centralizado (F22, M4)
File: app.py:9-20
Locations: app.py:9-20, routes/report_routes.py:182-188,204-209,217-223, routes/task_routes.py:13-63,146-154,217-223,231-238, routes/user_routes.py:80-90,127-132,144-151
Description: Nenhum tratador de erro é registrado na composição da aplicação em app.py:9-20. Cada handler traz o próprio bloco `try`, e os formatos divergem: `{'error': 'Erro interno'}` em routes/task_routes.py:63, `{'error': 'Erro ao criar task'}` em routes/task_routes.py:154, `{'error': 'Erro ao atualizar'}` em routes/task_routes.py:223 e em routes/report_routes.py:209. Onze handlers dos 22 não têm bloco algum e qualquer falha neles devolve o rastreamento do Werkzeug, por causa de F02.
Impact: O formato do corpo de erro depende de qual handler falhou. Acrescentar um endpoint exige replicar o bloco. Endpoints sem bloco devolvem um corpo diferente dos que têm bloco para a mesma classe de falha.
Recommendation: Registrar um tratador central de exceção no ponto de entrada, com a guarda `isinstance(exc, HTTPException)` para preservar 404 de caminho inexistente e 405 de método não permitido, e remover os blocos genéricos dos handlers. Aplicar T11.

### [MEDIUM] Ponto de entrada com responsabilidades além da composição (F23, MVC)
File: app.py:11-13,22-31
Description: O ponto de entrada acumula quatro responsabilidades que não são composição: configuração por literal em 11-13, definição de duas rotas em 22-28, formatação do corpo de resposta dessas rotas em 24 e 28, e criação de esquema em 30-31. O bloco `with app.app_context(): db.create_all()` está no corpo do módulo, portanto executa em todo import, inclusive no `from app import app, db` de seed.py:2.
Impact: Importar `app` cria o esquema como efeito colateral. As duas rotas definidas aqui não passam pela camada de rotas, portanto o inventário de endpoints está dividido entre quatro arquivos.
Recommendation: Reduzir o arquivo da raiz a um carregador, mover a composição para uma fábrica de aplicação, mover as duas rotas para a camada de rotas com os handlers na camada de controllers, e mover a criação de esquema para a fábrica. Aplicar T15.

### [MEDIUM] Importação não utilizada e métodos mortos no modelo de task (F24, M5)
File: models/task.py:3,38-48
Description: `import json` na linha 3 não é referenciado no arquivo. Os métodos `validate_status` em 38-43 e `validate_priority` em 45-48 não são chamados em nenhum arquivo do projeto, embora a mesma validação exista por extenso em routes/task_routes.py:110, 113, 177 e 182.
Impact: A leitura do modelo sugere que a validação de status e de prioridade passa por ele, quando na verdade passa pelos handlers. Uma correção aplicada nesses métodos não teria efeito.
Recommendation: Remover a importação e, ao aplicar F26 e F36, passar a usar os métodos em vez de removê-los; se a validação for consolidada em outro ponto, remover os métodos. Aplicar T12.

### [MEDIUM] API obsoleta: datetime.utcnow() (F25, M6)
File: models/task.py:15,16,52
Locations: models/category.py:11, models/task.py:15,16,52, models/user.py:14, routes/report_routes.py:35,42,45,71,133, routes/task_routes.py:31,72,215,285, routes/user_routes.py:172, seed.py:66,67,69,70,74, services/notification_service.py:35, utils/helpers.py:38
Description: `datetime.utcnow()` está depreciado desde Python 3.12 conforme a documentação oficial da biblioteca padrão. Ocorre 24 vezes em 8 arquivos, incluindo os valores padrão das colunas `created_at` e `updated_at` dos três modelos. O projeto não declara versão de Python em `requires-python`, `python_requires` nem arquivo de versão, portanto a constatação não é suprimida. O interpretador observado nesta máquina é Python 3.9.6, obtido com `python3 --version`, e esse dado não suprime a constatação.
Impact: A remoção em versão futura quebra a criação de registros nos três modelos. O valor devolvido é ingênuo, sem fuso, o que já hoje impede comparação com valor com fuso e levantaria `TypeError`.
Recommendation: Substituir por `datetime.now(timezone.utc).replace(tzinfo=None)`, que preserva exatamente o valor sem fuso que as colunas persistem, encapsulado em uma função nomeada usada como padrão de coluna. Aplicar T14.

### [MEDIUM] Cálculo de atraso duplicado em cinco pontos (F26, M2)
File: models/task.py:50-60
Locations: models/task.py:50-60, routes/report_routes.py:33-37,132-135, routes/task_routes.py:30-39,71-80,283-287, routes/user_routes.py:171-180
Description: `Task.is_overdue()` implementa a regra de atraso em models/task.py:50-60 e não é chamado em nenhum arquivo do projeto. O mesmo aninhamento de três condições aparece escrito por extenso em cinco handlers, em três arquivos.
Impact: Uma correção na regra de atraso precisa ser aplicada em seis pontos. Um ponto esquecido produz valor de `overdue` divergente entre `GET /tasks`, `GET /tasks/<id>`, `GET /tasks/stats`, `GET /users/<id>/tasks` e `GET /reports/summary`.
Recommendation: Reusar `Task.is_overdue()` nos cinco pontos e chamá-lo dentro de `Task.to_dict()`. Aplicar T10.

### [MEDIUM] Importações não utilizadas nos handlers de relatório (F27, M5)
File: routes/report_routes.py:7-8
Description: `from utils.helpers import format_date, calculate_percentage` na linha 7 traz duas funções, e nenhuma das duas é chamada no arquivo. `import json` na linha 8 não é referenciado.
Impact: A linha 7 sugere que o arquivo delega formatação de data e cálculo de porcentagem ao módulo de apoio, quando na verdade recalcula ambos por extenso nas linhas 41, 67 e 151.
Recommendation: Remover a importação de `json` e, ao aplicar F29, passar a usar `calculate_percentage` em vez de removê-la. Aplicar T12.

### [MEDIUM] Consulta dentro de laço na produtividade por usuário (F28, M1)
File: routes/report_routes.py:55-68
Description: O laço sobre os usuários carregados em 53 executa `Task.query.filter_by(user_id=u.id).all()` na linha 56, uma consulta por usuário.
Impact: `GET /reports/summary` executa 1 consulta de usuários mais N consultas de tarefas, com N igual ao número de usuários. O número de idas ao banco cresce com o cadastro.
Recommendation: Substituir por consulta única com agregação por usuário, ou por carga antecipada do relacionamento. Aplicar T7.

### [MEDIUM] Cálculo de taxa de conclusão duplicado (F29, M2)
File: routes/report_routes.py:67,151
Locations: routes/report_routes.py:67, routes/report_routes.py:151, routes/task_routes.py:296, utils/helpers.py:14-17
Description: A expressão `round((done / total) * 100, 2) if total > 0 else 0` aparece em três handlers. A função `calculate_percentage` em utils/helpers.py:14-17 implementa exatamente o mesmo cálculo, é importada em routes/report_routes.py:7 e não é chamada em nenhum lugar.
Impact: Uma mudança na precisão ou no tratamento do divisor zero precisa ser aplicada em quatro pontos. Um ponto esquecido produz taxa divergente entre `GET /tasks/stats`, `GET /reports/summary` e `GET /reports/user/<id>`.
Recommendation: Reusar `calculate_percentage` nos três handlers, preservando `round(..., 2)` e o retorno `0` para total zero. Aplicar T10.

### [MEDIUM] Consulta dentro de laço na listagem de categorias (F30, M1)
File: routes/report_routes.py:161-164
Description: O laço sobre as categorias carregadas em 159 executa `Task.query.filter_by(category_id=c.id).count()` na linha 163, uma consulta por categoria.
Impact: `GET /categories` executa 1 consulta de categorias mais N consultas de contagem, com N igual ao número de categorias.
Recommendation: Substituir por consulta única com contagem agrupada por `category_id`. Aplicar T7.

### [MEDIUM] Validação ausente nos handlers de categoria (F31, M3) [contract-breaking]
File: routes/report_routes.py:180,196-202
Description: `create_category` atribui `data.get('color', '#000000')` na linha 180 sem verificar o formato, enquanto `is_valid_color` existe em utils/helpers.py:52-55 e não é chamada. `update_category` em 196-202 não valida nada: aceita qualquer valor para `name`, `description` e `color`, inclusive nome vazio, que `create_category` recusa na linha 175.
Impact: Uma categoria pode ser criada com `color` igual a qualquer texto e atualizada para nome vazio. Os dois estados são persistidos e devolvidos por `GET /categories`, e o segundo é um estado que a rota de criação recusa.
Recommendation: Chamar `is_valid_color` no caminho de escrita das duas rotas e aplicar em `update_category` a mesma verificação de nome obrigatório que `create_category` já faz. Aplicar T20.
Contract change: `POST /categories` passa a devolver 400 para `color` fora do formato `#RRGGBB`, hoje aceito com 201. `PUT /categories/<id>` passa a devolver 400 para nome vazio e para `color` fora do formato, hoje aceitos com 200.

### [MEDIUM] Importações não utilizadas nos handlers de task (F32, M5)
File: routes/task_routes.py:7
Description: `import json, os, sys, time` traz quatro símbolos e nenhum dos quatro é referenciado no arquivo.
Impact: A linha sugere dependências de sistema operacional, de serialização e de tempo que o arquivo não tem.
Recommendation: Remover a linha inteira. Aplicar T12.

### [MEDIUM] API obsoleta: Model.query e Query.get (F33, M6)
File: routes/task_routes.py:14,42,51,67,117,122,158,188,195,227,247,275-281
Locations: routes/report_routes.py:15-56,105,109,159,163,192,213, routes/task_routes.py:14,42,51,67,117,122,158,188,195,227,247,275-281, routes/user_routes.py:12,29,35,67,94,109,136,140,155,159,197, seed.py:11-13,94-96
Description: `Model.query` é interface legada em Flask-SQLAlchemy 3.1 e `Query.get(pk)` é legado desde SQLAlchemy 2.0, conforme a documentação oficial dos dois projetos. O projeto declara `flask-sqlalchemy==3.1.1` em requirements.txt. Ocorrem 66 usos de `Model.query` em 4 arquivos, dos quais 13 são `Query.get`.
Impact: A remoção em versão futura quebra todos os 22 endpoints e o script de carga inicial. `Query.get` já emite aviso de depreciação legada em SQLAlchemy 2.0.
Recommendation: Substituir `Model.query.get(pk)` por `db.session.get(Model, pk)`, `Model.query.all()` por `db.session.execute(db.select(Model)).scalars().all()`, `Model.query.filter_by(...)` por `db.select(Model).where(...)` e `Model.query.count()` pela contagem por `db.func.count()`. Aplicar T14.

### [MEDIUM] Serialização de task reimplementada nos handlers (F34, M2)
File: routes/task_routes.py:17-28
Locations: routes/task_routes.py:17-28, routes/user_routes.py:162-169
Description: `get_tasks` monta o dicionário da tarefa campo por campo em 17-28, reproduzindo exatamente o corpo de `Task.to_dict()` de models/task.py:23-36. `get_user_tasks` monta um subconjunto dos mesmos campos em 162-169. Os demais handlers usam `to_dict()`.
Impact: Acrescentar um campo ao modelo exige editar três pontos. Um ponto esquecido faz `GET /tasks` e `GET /tasks/<id>` devolverem conjuntos de chaves diferentes para a mesma entidade.
Recommendation: Reusar `Task.to_dict()` em `get_tasks` e derivar o subconjunto de `get_user_tasks` da mesma serialização, preservando exatamente as chaves que cada endpoint devolve hoje. Aplicar T10.

### [MEDIUM] Consulta dentro de laço na listagem de tasks (F35, M1)
File: routes/task_routes.py:41-57
Description: O laço sobre as tarefas carregadas em 14 executa `User.query.get(t.user_id)` na linha 42 e `Category.query.get(t.category_id)` na linha 51, duas consultas por tarefa.
Impact: `GET /tasks` executa 1 consulta de tarefas mais até 2N consultas de resolução de nome, com N igual ao número de tarefas. Os relacionamentos `Task.user` e `Task.category` já estão declarados em models/task.py:20-21 e não são usados.
Recommendation: Substituir por carga antecipada dos relacionamentos com `joinedload`, preservando `None` como valor para identificador ausente ou registro inexistente. Aplicar T7.

### [MEDIUM] Validação sem verificação de tipo nos handlers de task (F36, M3) [contract-breaking]
File: routes/task_routes.py:96-100,113-114,166-170,181-184,260-264
Description: `create_task` compara `len(title)` em 96 e 99 e `priority < 1 or priority > 5` em 113 sem verificar o tipo dos valores recebidos. `update_task` repete as duas comparações em 167, 169 e 182. `search_tasks` chama `int(priority)` em 261 e `int(user_id)` em 264 sobre argumentos de consulta. A função `process_task_data` em utils/helpers.py:57-108 faz a conversão de tipo dentro de bloco protegido e não é chamada em nenhum lugar.
Impact: `POST /tasks` com `{"title":"abc","priority":"alta"}` levanta `TypeError` na comparação da linha 113 e, como não há tratador central e o modo de depuração está ativo por F02, a resposta é o rastreamento do Werkzeug com status 500 em vez de 400. `GET /tasks/search?priority=alta` levanta `ValueError` na linha 261. `POST /tasks` com `{"title":123}` levanta `TypeError` na linha 96.
Recommendation: Verificar o tipo antes de comparar, nos cinco pontos, reusando a conversão protegida de `process_task_data`. A biblioteca `marshmallow` já está declarada em requirements.txt e pode ser usada sem introduzir dependência nova. Aplicar T20.
Contract change: `POST /tasks` e `PUT /tasks/<id>` passam a devolver 400 com corpo `{"error": ...}` para `title` ou `priority` de tipo inválido, hoje respondidos com 500. `GET /tasks/search` passa a devolver 400 para `priority` ou `user_id` não numérico, hoje respondido com 500. Nenhuma dessas entradas é persistida hoje, portanto nenhum dado existente é invalidado.

### [MEDIUM] Importações não utilizadas nos handlers de usuário (F37, M5)
File: routes/user_routes.py:6
Description: `import hashlib, json, re` traz três símbolos. Apenas `re` é referenciado, nas linhas 61 e 106. `hashlib` e `json` não são referenciados no arquivo.
Impact: A presença de `hashlib` sugere que o arquivo manipula digest de senha diretamente, quando na verdade delega a `User.set_password`.
Recommendation: Reduzir a linha a `import re`. Aplicar T12.

### [MEDIUM] Validação ausente na atualização de usuário (F38, M3) [contract-breaking]
File: routes/user_routes.py:102-103
Description: `update_user` atribui `user.name = data['name']` na linha 103 sem nenhuma verificação, enquanto `create_user` exige nome não vazio na linha 54. O mesmo handler valida email, senha e role, portanto a lacuna é apenas no campo `name`.
Impact: Um usuário pode ser atualizado com `name` igual a string vazia, `None` ou número, estado que `POST /users` recusa com 400. O valor é persistido e devolvido por `GET /users` e `GET /users/<id>`.
Recommendation: Aplicar em `update_user` a mesma verificação de nome obrigatório que `create_user` já faz. Aplicar T20.
Contract change: `PUT /users/<id>` passa a devolver 400 com corpo `{"error": "Nome é obrigatório"}` para `name` vazio ou ausente de valor, hoje aceito com 200.

### [MEDIUM] Módulo de serviço morto (F39, M5)
File: services/notification_service.py:1-48
Description: A classe `NotificationService` não é importada nem instanciada em nenhum arquivo do projeto. A busca por `NotificationService` devolve uma única ocorrência, a própria declaração na linha 4. O módulo contém 48 linhas com transporte de email, regra de notificação e consulta de registro.
Impact: A leitura do projeto sugere que atribuição de tarefa e tarefa atrasada disparam notificação, o que não acontece em nenhum dos 22 endpoints. O módulo mantém vivos no código-fonte a credencial de F09 e o acoplamento de F19.
Recommendation: Remover o módulo. Aplicar T12. A remoção encerra também F09, F19 e F51, cujas ocorrências existem apenas neste arquivo. A funcionalidade de notificação nunca foi ligada a nenhuma rota, portanto a remoção não retira comportamento observável; a ausência dessa funcionalidade é registrada aqui e não é implementada por conta própria, porque implementá-la alteraria comportamento.

### [MEDIUM] Código morto no módulo de apoio (F40, M5)
File: utils/helpers.py:2-7,19-41,52-116
Description: Os imports `re`, `os`, `json`, `sys`, `math` e `hashlib` nas linhas 2-7 incluem quatro não referenciados: `os`, `json`, `sys` e `math`. Sete funções não são chamadas em nenhum arquivo do projeto: `validate_email` em 19-23, `sanitize_string` em 25-29, `generate_id` em 31-34, `log_action` em 36-41, `is_valid_color` em 52-55, `process_task_data` em 57-108 e `format_date` em 9-12. Sete constantes nas linhas 110-116 também não são referenciadas em nenhum lugar, embora seus valores apareçam como literais em outros arquivos.
Impact: 84 das 116 linhas do arquivo não são alcançadas por nenhum caminho de execução. As constantes de 110-116 nomeiam exatamente os literais que os handlers repetem, portanto a leitura sugere que a padronização já existe.
Recommendation: Remover os imports não usados, `generate_id` e `sanitize_string`. As demais funções e constantes são o destino de F29, F31, F36 e F42: passar a usá-las em vez de removê-las. Aplicar T12 para o que sai e T13 para as constantes que passam a ser usadas.

### [LOW] Envelope de resposta inconsistente (F41, L4) [contract-breaking]
File: app.py:22-28
Locations: app.py:24,28, routes/report_routes.py:101,155,165,171,185,206,220, routes/task_routes.py:61,63,83,150,235, routes/user_routes.py:25,31,148,207-211
Description: Os endpoints do projeto usam quatro envelopes diferentes. As listagens devolvem array puro em routes/task_routes.py:61, routes/user_routes.py:25 e routes/report_routes.py:165. Os erros devolvem `{'error': ...}`. As confirmações devolvem `{'message': ...}` em routes/task_routes.py:235 e routes/user_routes.py:148. As duas rotas do ponto de entrada devolvem objetos com chaves próprias, `{'status','timestamp'}` em app.py:24 e `{'message','version'}` em app.py:28.
Impact: O cliente precisa de tratamento por endpoint em vez de tratamento único. Uma resposta de sucesso pode ser array, objeto de entidade ou objeto com a chave `message`, dependendo do endpoint.
Recommendation: A recomendação padrão é não aplicar. O ganho é de padronização e o custo é a quebra de todos os consumidores das 22 rotas. Aplicar T22 apenas se autorizado.
Contract change: Todos os 22 endpoints passam a devolver o envelope `{"dados": ..., "sucesso": true}` no sucesso e `{"erro": ..., "sucesso": false}` no erro. Os arrays puros das listagens passam a estar sob a chave `dados`, e a chave `error` passa a se chamar `erro`.

### [LOW] Lista de status válidos repetida em quatro arquivos (F42, L5)
File: models/task.py:39
Locations: models/task.py:39, routes/task_routes.py:110,177, utils/helpers.py:75,110
Description: A lista `['pending', 'in_progress', 'done', 'cancelled']` está escrita em cinco lugares, em quatro arquivos. A lista `['user', 'admin', 'manager']` está escrita em três lugares: routes/user_routes.py:71 e 120 e utils/helpers.py:111. O par terminal `'done'` e `'cancelled'` aparece em mais seis comparações do cálculo de atraso.
Impact: Acrescentar um status exige localizar cinco cópias. Cópias divergentes produzem validação inconsistente entre `POST /tasks` e `PUT /tasks/<id>`.
Recommendation: Consolidar em constante nomeada no módulo de configuração, reusando `VALID_STATUSES` e `VALID_ROLES` que utils/helpers.py:110-111 já define e ninguém importa, com os mesmos valores. Aplicar T13.

### [LOW] Parâmetro com nome de um caractere (F43, L2)
File: models/task.py:45
Description: O método `validate_priority(self, p)` nomeia o parâmetro `p`, que não é índice de laço.
Impact: O significado do parâmetro só é recuperável lendo o corpo do método.
Recommendation: Renomear para `priority`. Aplicar T21.

### [LOW] Faixa de prioridade como literal (F44, L1)
File: models/task.py:46
Description: A comparação `if p >= 1 and p <= 5` usa os literais 1 e 5 sem nome. Os mesmos limites aparecem em routes/task_routes.py:113 e 182, e o valor padrão 3 aparece em models/task.py:12 e routes/task_routes.py:104.
Impact: O significado dos limites não é recuperável pela leitura, e alterar a faixa exige localizar todas as ocorrências.
Recommendation: Extrair para constante nomeada no módulo de configuração, reusando `DEFAULT_PRIORITY` que utils/helpers.py:115 já define, preservando os valores 1, 5 e 3. Aplicar T13.

### [LOW] Nomes p1 a p5 nas contagens por prioridade (F45, L2)
File: routes/report_routes.py:24-28
Description: As cinco contagens por prioridade são atribuídas a `p1`, `p2`, `p3`, `p4` e `p5`, nomes de dois caracteres que não são índice de laço. As chaves de resposta correspondentes em 84-88 usam os nomes de negócio `critical`, `high`, `medium`, `low` e `minimal`.
Impact: A correspondência entre o número da prioridade e o nome de negócio só é recuperável comparando dois blocos separados por 60 linhas.
Recommendation: Renomear as variáveis para os nomes de negócio já usados nas chaves de resposta, ou derivar as contagens de uma estrutura que associe número e nome. As chaves de resposta não mudam. Aplicar T21.

### [LOW] Números mágicos nos handlers de relatório (F46, L1)
File: routes/report_routes.py:45,129
Description: `timedelta(days=7)` na linha 45 define a janela de atividade recente, e `t.priority <= 2` na linha 129 define o limite de prioridade alta. Os dois valores aparecem como literais, e os nomes das chaves de resposta `tasks_created_last_7_days` e `high_priority` repetem o significado.
Impact: O significado dos valores não é recuperável pela leitura da comparação, e alterar a janela exige editar a expressão e o nome da chave de resposta.
Recommendation: Extrair para constante nomeada no módulo de configuração, preservando os valores 7 e 2. Aplicar T13.

### [LOW] Números mágicos de título e prioridade nos handlers de task (F47, L1)
File: routes/task_routes.py:96,99,113,167,169,182
Description: Os literais 3 e 200 delimitam o tamanho do título em 96, 99, 167 e 169. Os literais 1 e 5 delimitam a prioridade em 113 e 182. As constantes `MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH` e `DEFAULT_PRIORITY` existem em utils/helpers.py:112-115 com exatamente esses valores e não são importadas.
Impact: Alterar o tamanho máximo do título exige localizar quatro ocorrências em dois handlers, além da declaração da coluna em models/task.py:9.
Recommendation: Reusar as constantes que utils/helpers.py já define, movidas para o módulo de configuração, preservando os valores. Aplicar T13.

### [LOW] Saída em terminal como registro de log nos handlers de task (F48, L3)
File: routes/task_routes.py:149,153,219,234
Description: Quatro chamadas a `print` registram criação, falha de criação, atualização e remoção de tarefa, sem nível de severidade e sem destino configurável.
Impact: Não há como filtrar por severidade nem direcionar a saída para um coletor. A mensagem da linha 153 registra a causa de uma exceção no mesmo canal de uma mensagem informativa.
Recommendation: Substituir por registro com nível, usando o módulo `logging` da biblioteca padrão, com `logger.info` para as três mensagens informativas e `logger.exception` para a falha. Aplicar T23.

### [LOW] Tamanho mínimo de senha como literal (F49, L1)
File: routes/user_routes.py:64,115
Description: A comparação `len(password) < 4` em 64 e `len(data['password']) < 4` em 115 usa o literal 4. A constante `MIN_PASSWORD_LENGTH = 4` existe em utils/helpers.py:114 e não é importada. As duas mensagens de erro divergem: `'Senha deve ter no mínimo 4 caracteres'` em 65 e `'Senha muito curta'` em 116.
Impact: Alterar a política de senha exige editar dois pontos e duas mensagens. O valor 4 aparece na mensagem como texto, portanto a mudança exige editar também o literal da mensagem.
Recommendation: Reusar `MIN_PASSWORD_LENGTH`, movida para o módulo de configuração, preservando o valor 4 e as duas mensagens atuais sem alteração. Aplicar T13.

### [LOW] Saída em terminal como registro de log nos handlers de usuário (F50, L3)
File: routes/user_routes.py:83,89,147
Description: Três chamadas a `print` registram criação de usuário, causa de exceção e remoção de usuário, sem nível de severidade e sem destino configurável.
Impact: Não há como filtrar por severidade nem direcionar a saída para um coletor. A mensagem da linha 89 envia a causa de uma exceção para o mesmo canal das mensagens informativas.
Recommendation: Substituir por registro com nível, usando o módulo `logging` da biblioteca padrão, com `logger.info` para as duas mensagens informativas e `logger.exception` para a falha. Aplicar T23.

### [LOW] Saída em terminal como registro de log no serviço de notificação (F51, L3)
File: services/notification_service.py:21,24
Description: Duas chamadas a `print` registram o envio de email e a causa da falha de envio, sem nível de severidade e sem destino configurável.
Impact: Não há como filtrar por severidade nem direcionar a saída para um coletor. A mensagem da linha 21 registra o endereço de destino em canal não configurável.
Recommendation: A remoção do módulo prevista em F39 encerra esta constatação. Caso o módulo seja mantido, substituir por registro com nível. Aplicar T23.

### [LOW] Nomes sem significado no módulo de apoio (F52, L2)
File: utils/helpers.py:25,83
Description: `sanitize_string(s)` nomeia o parâmetro `s` na linha 25, e `process_task_data` atribui o resultado da conversão de prioridade à variável `p` na linha 83. Nenhum dos dois é índice de laço.
Impact: O significado do parâmetro e da variável só é recuperável lendo o corpo da função.
Recommendation: Renomear `s` para `value` e `p` para `priority`. Aplicar T21.

### [LOW] Saída em terminal como registro de log no módulo de apoio (F53, L3)
File: utils/helpers.py:39,41
Description: A função `log_action` implementa registro de log com duas chamadas a `print`, sem nível de severidade e sem destino configurável. A função não é chamada em nenhum arquivo do projeto.
Impact: A presença de uma função chamada `log_action` sugere que o projeto tem registro de log centralizado, quando os handlers usam `print` direto. Não há como filtrar por severidade nem direcionar a saída.
Recommendation: A remoção prevista em F40 encerra esta constatação. Caso a função seja mantida como fachada de registro, reimplementá-la sobre o módulo `logging`. Aplicar T23.

================================
Total: 53 findings
================================

================================
ADDENDUM: FINDINGS FROM THE PHASE 3 RE-AUDIT
================================
As três constatações abaixo não estão entre as 53 da Fase 2. Foram encontradas na passagem B da re-auditoria do passo 3.5, sobre o código já refatorado, e confirmadas por leitura do commit 6d1ce62 como pré-existentes ao código original, portanto não são regressão introduzida pela refatoração. A numeração segue a do relatório. As três foram autorizadas em portão estreito e aplicadas.

## Summary
CRITICAL: 0 | HIGH: 1 | MEDIUM: 2 | LOW: 0

## Findings

### [HIGH] Troca de senha sem verificação de identidade (F54, C4) [contract-breaking]
File: routes/user_routes.py:92-118
Description: `PUT /users/<id>` altera a senha de qualquer conta sem nenhuma verificação de identidade. Reproduzido por execução: `PUT /users/1` com corpo `{"password":"tomada9999"}` e sem cabeçalho algum devolve 200, e o `POST /login` seguinte com a senha nova devolve 200 com o token do usuário 1. O projeto define `User.is_admin()` e nunca o chama, e o token devolvido pelo login é a concatenação de um prefixo fixo com o identificador, não verificado em endpoint algum.
Impact: Qualquer cliente com acesso de rede assume permanentemente a conta de qualquer usuário, inclusive a de papel `admin`. A rota de remoção já exigia credencial, portanto a rota de atualização era o caminho mais barato para o mesmo resultado.
Recommendation: Aplicar a mesma guarda de credencial administrativa usada nos três `DELETE`. Aplicar T16, opção B.
Contract change: `PUT /users/<id>` passa a devolver 401 com corpo `{"erro": "Não autorizado", "sucesso": false}` para requisição sem o cabeçalho de credencial. Com credencial válida, corpo e status permanecem idênticos.

### [MEDIUM] Atualização de categoria sem guarda de corpo (F55, M3) [contract-breaking]
File: routes/report_routes.py:190-202
Description: `update_category` lê o corpo e usa `'name' in data` sem verificar se o corpo existe, enquanto os outros cinco handlers de escrita do projeto verificam. Reproduzido: corpo JSON `null` devolve 500 com `argument of type 'NoneType' is not iterable`, e corpo `{}` devolve 200 e grava, onde os handlers irmãos devolvem 400.
Impact: A mesma classe de entrada produz três respostas diferentes conforme o endpoint: 400 nos cinco handlers com guarda, 500 e 200 neste. O 500 expõe uma falha interna para entrada que é erro de cliente.
Recommendation: Acrescentar a guarda de corpo que os cinco handlers irmãos já aplicam. Aplicar T20.
Contract change: `PUT /categories/<id>` passa a devolver 400 para corpo vazio, hoje aceito com 200, e para corpo nulo, hoje respondido com 500.

### [MEDIUM] Corpo JSON não-objeto nos handlers de escrita (F56, M3) [contract-breaking]
File: routes/task_routes.py:85-92,156-165
Locations: routes/report_routes.py:167-175, routes/task_routes.py:85-92,156-165, routes/user_routes.py:42-48,92-101,185-190
Description: A guarda `if not data` aprova qualquer valor verdadeiro, então um corpo JSON válido que não seja objeto atravessa a verificação. Reproduzido: `POST /tasks` com corpo `"abc"` devolve 500 com `'str' object has no attribute 'get'`, e `PUT /users/1` com corpo `[1,2]` devolve 200 sem alterar campo algum.
Impact: Erro de cliente produz 5xx em um caminho e sucesso silencioso em outro. O 200 sobre entrada malformada é o pior dos dois, porque o cliente recebe confirmação de uma escrita que não ocorreu.
Recommendation: Verificar que o corpo é objeto antes de usá-lo, em ponto único consumido pelos seis handlers de escrita. Aplicar T20.
Contract change: `POST /tasks`, `PUT /tasks/<id>`, `POST /users`, `PUT /users/<id>`, `POST /login`, `POST /categories` e `PUT /categories/<id>` passam a devolver 400 para corpo JSON que não seja objeto, hoje respondido com 500 ou com 200.

================================
Addendum total: 3 findings
Relatório completo: 53 findings da Fase 2 mais 3 do adendo = 56
================================
