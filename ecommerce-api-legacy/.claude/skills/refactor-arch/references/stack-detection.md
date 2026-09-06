# Detecção de stack e mapeamento de arquitetura

## Conteúdo

- Ordem de precedência
- Detecção de linguagem
- Detecção de framework e versão
- Detecção de banco de dados e tabelas
- Inventário de rotas
- Escopo de código-fonte do projeto
- Contagem de arquivos e linhas
- Classificação da arquitetura atual
- Derivação do domínio
- Stack fora das tabelas
- Preenchimento do bloco da Fase 1

## Ordem de precedência

Aplicar nesta ordem. A primeira evidência encontrada decide; as demais servem
para confirmar.

1. Arquivo de manifesto de dependências.
2. Extensão predominante dos arquivos-fonte.
3. Importações no ponto de entrada.
4. Conteúdo dos arquivos de código.

Nunca decidir por nome de diretório isolado. Um diretório chamado `models/` não
prova que existe camada de modelo.

## Detecção de linguagem

| Sinal | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python |
| `package.json` | JavaScript ou TypeScript |
| `tsconfig.json` presente junto de `package.json` | TypeScript |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java |
| `composer.json` | PHP |
| `Gemfile` | Ruby |
| `*.csproj`, `*.sln` | C# |

Se houver mais de um manifesto, tratar como projeto multi-linguagem e rodar as
três fases por subprojeto, um de cada vez.

## Detecção de framework e versão

A versão vem sempre do manifesto de dependências, nunca do código.

| Sinal no código | Framework | Onde ler a versão |
|---|---|---|
| `from flask import`, `Flask(__name__)` | Flask | linha `flask==` |
| `from fastapi import`, `FastAPI()` | FastAPI | linha `fastapi==` |
| `from django.` | Django | linha `django==` |
| `require('express')`, `from 'express'` | Express | `dependencies.express` |
| `require('fastify')` | Fastify | `dependencies.fastify` |
| `@nestjs/core` | NestJS | `dependencies["@nestjs/core"]` |
| `gin.Default()` | Gin | `go.mod` |
| `@SpringBootApplication` | Spring Boot | `pom.xml` |

Se o manifesto usar faixa (`^4.18.2`, `~3.1`), reportar a faixa declarada, não a
versão instalada, salvo quando houver arquivo de trava (`package-lock.json`,
`poetry.lock`) legível. Nesse caso, reportar a versão travada e indicar a
origem.

## Detecção de banco de dados e tabelas

| Sinal | Banco |
|---|---|
| `sqlite3.connect(...)`, `new sqlite3.Database(...)` | SQLite |
| `sqlite:///` em URI | SQLite via ORM |
| `psycopg`, `pg`, `postgresql://` | PostgreSQL |
| `mysql`, `pymysql`, `mysql://` | MySQL ou MariaDB |
| `mongoose`, `pymongo`, `mongodb://` | MongoDB |
| `redis` | Redis |

Extrair o caminho ou o host do literal de conexão e registrá-lo.

Tabelas, por ordem de confiabilidade:

1. Comandos `CREATE TABLE` no código ou em migrações.
2. Declarações de modelo do ORM com `__tablename__`, `tableName` ou
   equivalente.
3. Nomes de tabela citados em consultas literais.

Se as três fontes divergirem, reportar a união e indicar a divergência.

## Inventário de rotas

| Sinal | Framework |
|---|---|
| `@app.route(...)`, `@<bp>.route(...)` | Flask |
| `app.add_url_rule(path, endpoint, view, methods=[...])` | Flask |
| `Blueprint(...)` mais `register_blueprint(...)` | Flask |
| `app.get/post/put/patch/delete(path, handler)` | Express |
| `router.get/post/...` mais `app.use(prefix, router)` | Express |
| `@app.get(...)`, `@router.post(...)` | FastAPI |
| `path(...)`, `re_path(...)` em `urls.py` | Django |

Registrar para cada rota: método, caminho completo com prefixo de blueprint ou
router aplicado, e o nome do handler. Um caminho registrado duas vezes com
métodos diferentes conta como duas rotas.

Este inventário é o contrato preservado pela Fase 3.

## Escopo de código-fonte do projeto

Esta seção define, uma única vez, o conjunto de arquivos que toda operação sobre
o projeto inteiro pode ler. Quatro operações citam esta definição por nome: a
contagem do passo 1.3, a varredura de detecção do passo 2.1, a varredura de
resíduo de T2 em `refactoring-playbook.md`, e a passagem B da re-auditoria em
`remediation-protocol.md`.

O escopo é o conjunto de arquivos sob a raiz do projeto, menos as exclusões
abaixo, mais os arquivos de configuração versionados. É critério, não lista
congelada: é reavaliado a cada uso, de modo que arquivo criado ou movido pela
Fase 3 entra automaticamente.

Exclusões:

- diretórios de dependência (`node_modules/`, `.venv/`, `venv/`,
  `site-packages/`);
- artefatos (`__pycache__/`, `dist/`, `build/`, `*.pyc`);
- arquivos de trava (`package-lock.json`, `poetry.lock`, `yarn.lock`);
- arquivos de dados gerados (`*.db`, `*.sqlite`);
- `.git/`;
- `reports/`, que guarda a saída da própria Fase 2;
- `.refactor-arch/`, que guarda os artefatos de trabalho;
- o diretório da própria skill.

**O diretório da skill é resolvido pela convenção da ferramenta em uso**, em
Claude Code `.claude/`, nunca por uma regra do tipo "diretório que começa com
ponto". O enunciado do desafio manda copiar o diretório da skill para dentro de
cada projeto, e admite ferramentas cuja pasta de convenção não começa com ponto.
Sem essa exclusão, a skill audita os próprios exemplos.

Esta exclusão não é teórica. Buscar o literal de exemplo
`minha-chave-super-secreta-123` na árvore de um projeto real, sem o escopo,
devolve cinco ocorrências: três em `references/` da própria skill, uma no
relatório em `reports/`, e apenas uma no código do projeto. Quatro falsos
positivos para um verdadeiro. Uma verificação enunciada como "buscar no projeto
inteiro" sem este escopo treina quem lê a desconsiderar o resultado, que é
exatamente o oposto do que ela existe para fazer.

Recorte explícito: arquivo de configuração versionado **está** no escopo. Um
`.env` comitado ou uma fixture com credencial é constatação. Arquivo que a
própria T2 mandou passar a ignorar no versionamento fica fora.

Guardas para busca textual, para que a varredura não quebre nem produza falso
positivo nos artefatos de captura e no arquivo de banco:

- pular arquivo cujos primeiros 8 KB contenham byte nulo;
- pular arquivo acima de cerca de 2 MB.

## Contagem de arquivos e linhas

Contar apenas arquivos-fonte da linguagem detectada, dentro do escopo de
código-fonte definido acima.

Arquivos `__init__.py` vazios contam como arquivo-fonte e devem aparecer na
contagem, porque fazem parte da estrutura de pacotes.

## Classificação da arquitetura atual

Avaliar dois eixos, separadamente.

**Eixo A, existência de diretórios de camada.** Verificar a presença de
diretórios ou módulos dedicados a: configuração, modelos, controladores,
rotas ou views, e middlewares.

**Eixo B, pureza de cada camada.** Para cada diretório encontrado, aplicar a
tabela `contém / não contém` de `mvc-architecture.md`. Um diretório que contém
responsabilidade de outra camada não conta como camada implementada.

Classificação resultante:

| Eixo A | Eixo B | Classificação |
|---|---|---|
| Nenhum diretório de camada | não se aplica | `sem camadas` |
| Alguns diretórios | qualquer camada impura | `camadas parciais` |
| Todos os diretórios | todas as camadas puras | `camadas completas` |

Registrar, em uma linha, a evidência: quantos arquivos, quais camadas faltam e
qual responsabilidade está fora do lugar.

Exemplos de linha de evidência:

```
Arquitetura:      sem camadas - 4 arquivos na raiz, SQL e roteamento no mesmo módulo
Arquitetura:      camadas parciais - models/ e routes/ existem, sem controllers/; regra de negócio dentro das rotas
```

`camadas parciais` não significa arquitetura adequada. A auditoria da Fase 2
roda com o mesmo rigor nos três níveis de classificação.

## Derivação do domínio

Combinar três fontes e escrever uma frase:

1. Nomes das tabelas.
2. Substantivos dos caminhos de rota.
3. Nomes das entidades do ORM.

Formato: `<tipo de aplicação> (<entidades principais>)`.

```
Domínio:          E-commerce API (produtos, pedidos, usuários)
Domínio:          LMS API com fluxo de checkout (users, courses, enrollments, payments)
Domínio:          Task Manager API (tasks, users, categories)
```

Não derivar o domínio do nome do diretório do projeto. O nome do diretório pode
não corresponder ao conteúdo.

## Stack fora das tabelas

As tabelas acima cobrem as stacks já encontradas. Elas não são a lista fechada
de stacks suportadas: a skill roda em qualquer projeto que fale HTTP.

Quando a linguagem ou o framework não aparecer nas tabelas:

1. Aplicar a mesma ordem de precedência. O manifesto de dependências continua
   sendo a primeira evidência, qualquer que seja o seu nome.
2. Registrar o que estiver evidenciado e marcar `desconhecido` apenas o que não
   estiver. Framework não identificado não impede detectar linguagem, rotas e
   tabelas.
3. Derivar o inventário de rotas do mecanismo que o próprio projeto usa,
   procurando onde caminho, método e handler aparecem associados.
4. Derivar o comando de boot do manifesto ou do README, conforme
   `mvc-architecture.md`, seção "Preservação do ponto de entrada". Esse comando
   alimenta o parâmetro `BOOT` do procedimento genérico de
   `validation-protocol.md`.
5. Manter os mesmos cinco diretórios de camada da convenção alvo, adotando a
   nomenclatura idiomática da linguagem.

Não interromper a execução por stack desconhecida. Interromper apenas quando
faltar o comando de boot ou a porta, porque sem eles não há validação.

## Preenchimento do bloco da Fase 1

| Campo | Origem |
|---|---|
| `Linguagem` | detecção de linguagem |
| `Framework` | nome mais versão do manifesto |
| `Dependências` | demais entradas do manifesto, sem o framework |
| `Domínio` | derivação do domínio |
| `Arquitetura` | classificação mais evidência em uma linha |
| `Arquivos-fonte` | contagem de arquivos-fonte |
| `Tabelas do banco` | tabelas detectadas |
| `Ponto de entrada` | arquivo mais comando de boot do README ou do manifesto |
| `Rotas` | total do inventário de rotas |
| `Linhas de código` | soma das linhas dos arquivos-fonte |

Campo sem evidência recebe `desconhecido`. Não estimar.
