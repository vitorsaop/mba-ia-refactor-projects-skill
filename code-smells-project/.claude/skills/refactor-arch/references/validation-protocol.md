# Protocolo de validação da Fase 3

## Conteúdo

- Objetivo
- Visão geral dos quatro passos
- Passo 1: preparar e capturar a linha de base
  - 1.0 Fixar o contrato de execução
  - 1.1 Montar o conjunto de requisições, cobrindo as regras de negócio
  - 1.2 Conferir que a porta está livre
  - 1.3 Levar o banco a um estado conhecido
  - 1.4 Subir a aplicação e confirmar a identidade do servidor
  - 1.5 Executar a captura
  - 1.6 Conferir a captura
  - 1.7 Encerrar a aplicação
- Passo 2: aplicar as transformações
- Passo 3: reexecutar
- Passo 4: comparar
- Procedimento genérico, para qualquer stack
- Receitas por stack, exemplos preenchidos
- Critério de aprovação
- Laço de correção
- Falhas frequentes

## Objetivo

Comprovar que o contrato HTTP e as regras de negócio observáveis não mudaram.
A comprovação é a comparação entre duas execuções do mesmo conjunto de
requisições: uma sobre o código original, outra sobre o código refatorado,
partindo do mesmo estado de banco.

Sem linha de base gravada, a Fase 3 não prossegue. Afirmação de que os
endpoints continuam funcionando, sem a comparação, não vale como validação.

## Visão geral dos quatro passos

```
1. Preparar e capturar     codigo original  ->  baseline.json
2. Aplicar                 transformacoes do playbook
3. Reexecutar              codigo refatorado ->  after.json
4. Comparar                baseline.json vs after.json  ->  aprovado ou reprovado
```

Todos os artefatos ficam em `.refactor-arch/`, na raiz do projeto: o conjunto de
requisições, o instantâneo do banco, as duas capturas, o plano de
transformação, a lista de cobertura e o ambiente isolado de dependências. O
comparador não fica aqui: ele é empacotado na própria skill, em
`scripts/compare.py`.

`.refactor-arch/` é diretório de trabalho, não faz parte do código entregue.
Acrescentar a linha `.refactor-arch/` ao `.gitignore` do projeto como parte do
passo 2, para que os artefatos não entrem no versionamento.

## Passo 1: preparar e capturar a linha de base

Executar antes da primeira edição, com o código ainda original.

### 1.0 Fixar o contrato de execução

Antes de qualquer comando, gravar `.refactor-arch/runtime.md` com os campos
abaixo. Todos são **lidos do projeto**, nunca assumidos. Os blocos dos passos
1.2 a 1.7 e do Passo 3 leem estes campos; o número `5000` que aparece nos
exemplos deste arquivo é o valor do projeto de referência, não um padrão.

| Campo | Como obter |
|---|---|
| `PORTA` | nesta ordem: literal na chamada de inicialização; configuração; porta que o processo é observado ocupando. Se as três falharem, `desconhecido`, e o protocolo para |
| `BASE_URL` | sempre `http://127.0.0.1:$PORTA` |
| `HOST_BIND` | evidência separada; pode ser `desconhecido`; não compõe `BASE_URL` |
| `BOOT` | comando de boot documentado, verbatim |
| `CAMINHO_PRONTIDAO` e `MARCADOR` | conforme o passo 1.4 |
| `ALVO_PARADA` | conforme o passo 1.7 |
| `ESTADO` | procedimento de banco decidido no passo 1.3, com o caminho real do artefato |

**`BASE_URL` usa o literal de loopback, nunca `localhost`.** Em macOS,
`localhost` pode resolver para `::1` enquanto o processo escuta em IPv4, e a
captura inteira sai com status `000` sem que a aplicação tenha qualquer
problema.

Porta ocupada interrompe o protocolo, conforme o passo 1.2. **Não existe ramo de
"capturar em outra porta".** O código original costuma trazer a porta como
literal; alterá-lo antes da linha de base invalida a própria linha de base.

### 1.1 Montar o conjunto de requisições

Criar `.refactor-arch/requests.tsv`, uma requisição por linha, com três campos
separados por tabulação: método, caminho, corpo. Usar `-` quando não houver
corpo.

Regras de montagem:

- Toda rota do inventário da Fase 1 aparece ao menos uma vez.
- Rota com parâmetro aparece com um valor existente e com um valor inexistente,
  para cobrir o caminho de sucesso e o de 404.
- Rota de escrita aparece com corpo válido e com corpo inválido, para cobrir o
  caminho de 201 ou 200 e o de 400.
- As requisições de escrita vêm depois das de leitura, para que as leituras
  observem o mesmo estado inicial nas duas execuções.
- Rota destrutiva, que apague dados em massa, vem por último.
- Se o projeto trouxer um arquivo de exemplos de requisição, incorporar esses
  casos.

**Cobrir as regras de negócio, não apenas as rotas.** Percorrer todas as rotas
não é o mesmo que exercitar todas as regras. Um endpoint que calcula sobre dados
agregados, sondado com o banco vazio, devolve zero em todos os campos e não
exercita nenhum ramo do cálculo. Uma alteração na fórmula passaria despercebida.

Para cada endpoint que calcula um valor derivado, aplicar três regras:

1. Listar os ramos de decisão do cálculo lendo o código: faixas, limites,
   comparações de status, condições de data.
2. Acrescentar as requisições de escrita necessárias para que os dados alcancem
   cada ramo.
3. Sondar o endpoint calculado **depois** dessas escritas, além da sondagem
   inicial com o banco vazio.

Exemplo. Um endpoint de relatório aplica desconto por faixa de faturamento, com
os limites 10000, 5000 e 1000. Sondá-lo apenas no início da sequência produz
faturamento zero e desconto zero. O conjunto precisa criar pedidos que levem o
faturamento a cada faixa e sondar o relatório após cada criação.

Registrar em `.refactor-arch/coverage.md` a lista de regras de negócio
identificadas e qual requisição exercita cada uma. Regra sem requisição
correspondente é lacuna conhecida e deve constar do bloco da Fase 3.

Exemplo:

```
GET	/produtos	-
GET	/produtos/1	-
GET	/produtos/99999	-
GET	/produtos/busca?q=mouse	-
POST	/produtos	{"nome":"Teste","preco":10.5,"estoque":3,"categoria":"geral"}
POST	/produtos	{"preco":10.5}
PUT	/produtos/1	{"nome":"Alterado","preco":11.0,"estoque":4}
DELETE	/produtos/99999	-
POST	/login	{"email":"admin@loja.com","senha":"admin123"}
POST	/login	{"email":"admin@loja.com","senha":"errada"}
GET	/health	-
```

### 1.2 Conferir que a porta está livre

Antes de subir a aplicação, confirmar que ninguém ocupa a porta configurada:

```bash
PORTA=5000
lsof -nP -iTCP:$PORTA -sTCP:LISTEN
```

Saída vazia libera o passo seguinte. Saída com processo interrompe o protocolo:
reportar o processo ocupante e pedir que o usuário o encerre. Não trocar a porta
da aplicação, porque isso altera o comando de boot documentado e viola a regra
permanente 6.

Este passo não é formalidade. Se outro servidor responder na porta, a captura é
concluída com códigos de status válidos vindos do servidor errado, e a
comparação aprova duas capturas igualmente inválidas. Em macOS, a porta 5000 é
ocupada por padrão pelo receptor AirPlay, atendido pelo processo `ControlCenter`,
que responde 403 a qualquer caminho. O ajuste fica em Ajustes do Sistema, Geral,
AirDrop e Handoff, Receptor AirPlay.

### 1.3 Levar o banco a um estado conhecido

Decisão ordenada. Aplicar o primeiro ramo que couber e registrar o resultado em
`runtime.md`.

**1. Script de carga inicial.** Se o projeto traz um script de carga, ou a
sequência documentada de execução nomeia um, esse script **é** o estado
conhecido. Executá-lo uma vez e só então copiar.

**2. Esquema do primeiro boot.** Só na ausência do script, o esquema criado no
primeiro boot conta como estado conhecido.

**3. Localizar o artefato.** O caminho a copiar **não** é lido do literal de
conexão. Extrair o nome do arquivo do literal e procurá-lo dentro do escopo de
código-fonte definido em `stack-detection.md`:

| Ocorrências | Significado |
|---|---|
| exatamente uma | é o artefato; gravar o caminho real em `runtime.md` |
| nenhuma | banco em memória; o passo 2 do Passo 3 fica sem efeito |
| mais de uma | interromper e perguntar qual é |

O caso "nenhuma" precisa estar escrito para que um leitor literal não trave
esperando um arquivo que não existe.

Um ORM resolve URI relativa contra o próprio diretório-base. Em Flask-SQLAlchemy
3.x, `sqlite:///tasks.db` aparece na pasta de instância da aplicação, não na
raiz do projeto, e `rm -f tasks.db` na raiz não apaga nada — o boot seguinte
reaproveita o banco antigo e a linha de base parte de estado desconhecido.

**4. Asserção de estado.** Ao menos um endpoint de leitura da linha de base
devolve coleção não vazia. Caso contrário a preparação falhou e a captura é
inválida. Projeto que legitimamente parte vazio registra a isenção em
`runtime.md`, com a evidência.

**5. Banco servido por processo externo.** Quando o sistema de arquivos não
copia o estado, o estado conhecido é o passo de carga reexecutado antes do Passo
3. Isso só é equivalente enquanto esse passo não gravar valor derivado do
instante de execução, condição julgada por leitura do script.

A cópia é o que garante que as duas execuções partem de dados idênticos. Sem
ela, valores de data gerados na criação do banco divergem e a comparação acusa
diferença que não vem da refatoração.

### 1.4 Subir a aplicação e confirmar a identidade do servidor

Subir com o comando documentado e aguardar até que a resposta comprove que quem
atende é a aplicação sob teste, não outro servidor na mesma porta:

```bash
BASE_URL="http://localhost:5000"
MARCADOR='"produtos"'      # trecho estável do corpo de um endpoint conhecido

<comando de boot documentado> > .refactor-arch/boot.log 2>&1 &
pronto=0
for i in $(seq 1 40); do
  corpo=$(curl -s --max-time 2 "$BASE_URL/" 2>/dev/null || true)
  if printf '%s' "$corpo" | grep -q "$MARCADOR"; then pronto=1; break; fi
  sleep 0.5
done
[ "$pronto" -eq 1 ] || { echo "aplicacao nao respondeu"; cat .refactor-arch/boot.log; exit 1; }
```

`CAMINHO_PRONTIDAO` é escolhido **no inventário de rotas da Fase 1**: uma rota de
leitura sem parâmetro, preferindo a raiz ou a verificação de saúde **quando o
inventário realmente as contiver**.

A existência de `/` não é presumida. Um projeto cujas rotas são todas
prefixadas, por exemplo sob `/api`, não tem raiz, e um laço que sonda `/` nunca
termina, mesmo com a aplicação sadia.

Dois testes de prontidão, nesta ordem. Registrar em `runtime.md` qual foi usado.

1. **Marcador no corpo**, quando a rota escolhida tem corpo estável.
2. **Identidade por processo**, quando não tem: o PID que escuta em `PORTA` é o
   processo iniciado por `BOOT` ou descendente dele, e um caminho do inventário
   devolve status diferente de `000`.

O segundo teste é mais fraco: ele distingue a aplicação de um servidor estranho
na porta, mas não distingue uma aplicação sadia de uma que subiu com o banco
vazio. A asserção de estado do passo 1.3 é a única rede nesse caso.

**O marcador precisa ser ASCII.** Serializadores JSON escapam caracteres
não-ASCII por padrão. O Flask faz isso: um valor escrito no código como
`Bem-vindo à API` chega ao cliente como a sequência de seis caracteres
`à` no lugar do `à`. A busca pelo texto acentuado falha mesmo com a
aplicação respondendo 200. Escolher como marcador um nome de chave ou um valor
sem acento, por exemplo `"produtos"` ou `"status"`.

Aguardar apenas que a conexão seja aceita não basta: qualquer servidor na porta
aceita conexão. A confirmação exige conteúdo reconhecível da aplicação.

### 1.5 Executar a captura

Percorrer o conjunto de requisições:

```bash
mkdir -p .refactor-arch
BASE_URL="http://localhost:5000"
OUT=".refactor-arch/baseline.json"

echo "[" > "$OUT"
first=1
while IFS=$'\t' read -r method req_path body; do
  [ -z "$method" ] && continue
  if [ "$body" = "-" ]; then
    resp=$(curl -s -w '\n%{http_code}' -X "$method" "$BASE_URL$req_path")
  else
    resp=$(curl -s -w '\n%{http_code}' -X "$method" "$BASE_URL$req_path" \
           -H 'Content-Type: application/json' -d "$body")
  fi
  http_status=$(printf '%s' "$resp" | tail -n1)
  payload=$(printf '%s' "$resp" | sed '$d')
  [ $first -eq 0 ] && echo "," >> "$OUT"
  first=0
  METHOD="$method" PATHV="$req_path" STATUS="$http_status" PAYLOAD="$payload" \
    python3 -c '
import json, os
try:
    body = json.loads(os.environ["PAYLOAD"])
except json.JSONDecodeError:
    body = os.environ["PAYLOAD"]
print(json.dumps({
    "method": os.environ["METHOD"],
    "path": os.environ["PATHV"],
    "status": int(os.environ["STATUS"]),
    "body": body,
}, ensure_ascii=False, sort_keys=True))' >> "$OUT"
done < .refactor-arch/requests.tsv
echo "]" >> "$OUT"
```

Corpo que não for JSON é gravado como texto. Isso cobre endpoints que devolvem
texto simples.

**Nomes de variável reservados.** O laço usa `req_path` e `http_status`, não
`path` e `status`. Em zsh, que é o shell padrão em macOS, `path` é um parâmetro
especial vinculado a `PATH`: atribuir `path=/produtos` substitui o `PATH` inteiro
e, a partir da primeira iteração, `curl`, `tail`, `sed` e `python3` passam a
falhar com `command not found`. E `status` é um sinônimo somente-leitura de `$?`:
a atribuição aborta com `read-only variable: status`. Os demais parâmetros
especiais do zsh a evitar em laços de shell são `argv`, `cdpath`, `fpath`,
`manpath`, `module_path` e `prompt`.

Gravar o laço em `.refactor-arch/capture.sh` e executá-lo com `bash`, em vez de
colar o texto na sessão interativa. Isso isola o laço do shell da sessão.

Este laço foi executado contra um projeto Flask real, com 27 requisições sobre
19 rotas, e produziu capturas idênticas em duas execuções consecutivas a partir
do mesmo instantâneo de banco.

### 1.6 Conferir a captura

`baseline.json` precisa ter uma entrada por linha de `requests.tsv`. Verificar
os três sinais de captura inválida:

| Sinal | Significado |
|---|---|
| `status` igual a `000` em alguma entrada | A aplicação não respondeu àquela requisição |
| Mesmo `status` em todas as entradas, inclusive nas de erro esperado | Outro servidor atendeu na porta |
| `body` vazio em toda entrada | O servidor que respondeu não é a aplicação |

Uma distribuição de status plausível tem variedade: sucesso nas leituras, 201
nas criações, 400 nas entradas inválidas, 404 nos identificadores inexistentes.
Distribuição uniforme é indício de captura inválida.

Não seguir para o passo 2 com captura inválida ou incompleta.

### 1.7 Encerrar a aplicação

```bash
pkill -f "<caminho do arquivo de entrada>"
sleep 1
lsof -nP -iTCP:$PORTA -sTCP:LISTEN >/dev/null 2>&1 \
  && { echo "porta ainda ocupada"; exit 1; } || echo "porta liberada"
```

`ALVO_PARADA` é derivado **do processo observado escutando na porta**: o PID
devolvido por `lsof` mais o PID pai obtido por `ps`. Encerrar os dois e
confirmar que a porta ficou livre. O padrão de linha de comando permanece como
substituto documentado onde não houver equivalente.

O motivo de não montar o alvo a partir do nome do arquivo de entrada: o processo
pode ter sido iniciado por um invólucro — um gerenciador de tarefas, um script
de ambiente — cuja linha de comando não contém esse nome. Nesse caso o padrão
não casa com nada, o processo sobrevive, e a captura seguinte responde a partir
do código antigo sem qualquer sinal de erro.

Encerrar pelo identificador do processo iniciado em segundo plano também não é
suficiente. Com o modo de depuração ativo, o Flask usa um recarregador que
executa a aplicação em um processo filho, indicado na saída pela linha
`Restarting with stat`. Encerrar o processo pai deixa o filho ocupando a porta,
e a próxima captura atende contra a versão antiga do código.

Sempre confirmar que a porta foi liberada antes de prosseguir.

## Passo 2: aplicar as transformações

Seguir a ordem de `refactoring-playbook.md`. Restaurar o banco a partir de
`.refactor-arch/db.snapshot` ao final, para que o passo 3 parta do mesmo estado
do passo 1.

## Passo 3: reexecutar

1. Conferir que a porta está livre, como no passo 1.2.
2. Restaurar `.refactor-arch/db.snapshot` sobre o arquivo de banco.
3. Subir a aplicação com o mesmo comando documentado, sem alteração, e confirmar
   a identidade do servidor como no passo 1.4.
4. Executar o mesmo laço do passo 1.5, gravando em `.refactor-arch/after.json`.
5. Encerrar a aplicação como no passo 1.7 e confirmar que a porta foi liberada.

6. Depois de a comparação do Passo 4 aprovar, executar **uma vez cada comando da
   sequência documentada de execução que não seja o comando de boot**, na ordem
   do README, com o interpretador isolado. Registrar em `runtime.md` comando,
   código de saída e primeira linha de erro. Restaurar `db.snapshot` em seguida,
   porque esses comandos alteram estado. Projeto sem script auxiliar registra
   `nenhum`.

   Motivo: um script de carga inicial que importa caminhos de módulo movidos
   pela Fase 3 falha somente aqui. O boot da aplicação não o exercita, a captura
   não o exercita, e o projeto é entregue com a carga inicial quebrada.

Usar exatamente o mesmo `requests.tsv` do passo 1.1. Alterar o conjunto entre as
duas execuções invalida a comparação.

Se o comando de boot precisar ser alterado para a aplicação subir, a validação
está reprovada por violação da regra permanente 6. Corrigir a estrutura, não o
comando.

## Passo 4: comparar

Executar o comparador empacotado nesta skill. Não copiar nem reescrever o
script: ele é determinístico e a transcrição introduz risco de divergência entre
projetos.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/compare.py" \
  .refactor-arch/baseline.json .refactor-arch/after.json
```

Quando a variável não estiver disponível, usar o caminho relativo à raiz do
projeto:

```bash
python3 .claude/skills/refactor-arch/scripts/compare.py \
  .refactor-arch/baseline.json .refactor-arch/after.json
```

Códigos de saída:

| Código | Significado |
|---|---|
| 0 | Nenhuma divergência relevante. Validação aprovada. |
| 1 | Ao menos uma divergência. Cada uma é impressa com o caminho da chave. |
| 2 | Uso incorreto, captura ausente, vazia ou com JSON inválido. |

Código 2 não é reprovação de comportamento: indica que a captura não pode ser
comparada. Refazer o passo 1 antes de concluir qualquer coisa.

### Correções autorizadas que alteram o contrato

Toda correção autorizada no portão que altere o contrato produz divergência por
definição. Sem declaração prévia, o comparador reprova exatamente a mudança que
o usuário mandou fazer, e a Fase 3 fica com um incentivo invertido: não aplicar
a correção passa na validação, aplicar reprova.

A declaração fica em `.refactor-arch/expected.json`, escrita no passo 3.2, e é
passada ao comparador:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/compare.py" \
  .refactor-arch/baseline.json .refactor-arch/after.json \
  --expected .refactor-arch/expected.json
```

O formato do arquivo está em `remediation-protocol.md`. O comparador o usa nos
dois sentidos:

| Situação | Resultado |
|---|---|
| divergência declarada e observada | autorizada, não reprova |
| divergência não declarada | reprova |
| divergência declarada e não observada | reprova |

A terceira linha é a que detecta a correção autorizada e não aplicada. A
mensagem é `autorizada e não observada`, com o identificador `F` da constatação.
A correção é aplicar a constatação, nunca remover a entrada do arquivo.

Chave volátil adicional específica do projeto é passada como argumento extra.
Exemplo, para um projeto que devolve um identificador de correlação por
requisição:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/compare.py" \
  .refactor-arch/baseline.json .refactor-arch/after.json request_id
```

Acrescentar chave à lista de voláteis reduz o rigor da comparação. Só fazer isso
quando o valor for comprovadamente gerado no momento da requisição, e registrar
a decisão no bloco da Fase 3.

## Procedimento genérico, para qualquer stack

As receitas da seção seguinte são exemplos preenchidos de um mesmo
procedimento. Elas não são a lista fechada de stacks suportadas. Para um projeto
cuja stack não aparece ali, preencher os seis parâmetros abaixo com fatos lidos
na Fase 1 e executar o mesmo protocolo, sem alteração.

| Parâmetro | De onde vem | Se não houver evidência |
|---|---|---|
| `BOOT` | comando de boot documentado, campo `Ponto de entrada` do bloco da Fase 1 | interromper: sem comando de boot não há validação |
| `BASE_URL` | esquema, host e porta em que a aplicação escuta, lidos do código de inicialização ou da configuração | interromper e perguntar |
| `PORTA` | a porta contida em `BASE_URL` | idem |
| `DEPS` | comando de instalação derivado do manifesto de dependências | pular, se o projeto não declarar dependências |
| `ESTADO` | artefato que guarda o estado inicial: arquivo de banco, diretório de dados, ou `nenhum` para banco em memória | `nenhum` |
| `PARADA` | padrão de linha de comando que identifica o processo da aplicação | o próprio `BOOT` |

Regras que não dependem de stack:

1. `PORTA` nunca é alterada para viabilizar a validação. Porta ocupada
   interrompe o protocolo, conforme o passo 1.2. Trocar a porta altera o
   comando de boot documentado e viola a regra permanente 6.
2. `ESTADO` igual a `nenhum` dispensa cópia e restauração, desde que a rotina de
   carga inicial use valores literais. Se ela derivar valores do instante de
   execução, as chaves afetadas entram na lista de voláteis do comparador.
3. `DEPS` instala em ambiente isolado dentro de `.refactor-arch/`, nunca no
   ambiente do projeto, e nunca acrescenta dependência ao manifesto.
4. A confirmação de identidade do passo 1.4 é obrigatória em qualquer stack. O
   que muda entre stacks é o comando de boot, não a exigência de comprovar quem
   respondeu.

O número `5000` que aparece nos exemplos deste arquivo é o valor de `PORTA` de
um projeto específico, não um padrão da skill.

### Ferramentas de apoio e substitutos

O protocolo usa `curl`, `lsof` e `pkill`, que existem em ambiente POSIX. Onde
não existirem, substituir pela alternativa disponível mantendo a mesma função. O
que importa é a função, não o nome do utilitário.

| Função | POSIX | Substituto |
|---|---|---|
| Emitir requisição e capturar corpo e status | `curl -s -w '\n%{http_code}'` | qualquer cliente HTTP que devolva corpo e código; em Windows, `curl.exe` acompanha o sistema |
| Descobrir quem escuta a porta | `lsof -nP -iTCP:$PORTA -sTCP:LISTEN` | `ss -ltnp`, `netstat -ano`, `Get-NetTCPConnection -LocalPort` |
| Encerrar a aplicação e seus processos filhos | `pkill -f "$PARADA"` | `taskkill /F /IM`, `Stop-Process`, ou encerrar o grupo de processos |

Registrar no bloco da Fase 3 qualquer substituição feita. Um substituto que não
alcance os processos filhos reintroduz a falha descrita no passo 1.7.

### Esqueleto dos passos 1.4 e 1.5 com os parâmetros

```bash
BOOT="<comando de boot documentado>"
BASE_URL="<esquema://host:porta>"
PORTA="<porta>"
MARCADOR='<trecho ASCII estável do corpo de uma rota de leitura>'

$BOOT > .refactor-arch/boot.log 2>&1 &
pronto=0
for i in $(seq 1 40); do
  corpo=$(curl -s --max-time 2 "$BASE_URL/" 2>/dev/null || true)
  if printf '%s' "$corpo" | grep -q "$MARCADOR"; then pronto=1; break; fi
  sleep 0.5
done
[ "$pronto" -eq 1 ] || { echo "aplicacao nao respondeu"; cat .refactor-arch/boot.log; exit 1; }
```

O laço de captura do passo 1.5 já é genérico: ele só conhece método, caminho,
corpo e código de status, que existem em qualquer stack que fale HTTP.

## Receitas por stack, exemplos preenchidos

O invariante é: **o conjunto de dependências exercitado é o que o projeto
declara, instalado sem acrescentar nem atualizar nada.** O isolamento é o meio,
onde o ecossistema oferece um; ele não é o invariante. A promessa de isolar tudo
dentro de `.refactor-arch/` só o caminho Python cumpre.

### Python com Flask, banco em arquivo

```bash
python3 -m venv .refactor-arch/venv
.refactor-arch/venv/bin/pip install -q -r requirements.txt

rm -f <arquivo>.db
.refactor-arch/venv/bin/python app.py > .refactor-arch/boot.log 2>&1 &
# aguardar com verificação de identidade, conforme o passo 1.4
cp <arquivo>.db .refactor-arch/db.snapshot
```

O arquivo de banco só existe depois que a aplicação executa a rotina de criação
de esquema. Copiar antes da confirmação de identidade produz erro de arquivo
inexistente.

Quando o projeto tiver script de carga inicial, executá-lo antes da cópia:

```bash
.refactor-arch/venv/bin/python seed.py
cp <arquivo>.db .refactor-arch/db.snapshot
```

Se o script de carga gravar datas relativas ao instante de execução, executá-lo
uma única vez, antes da cópia. As duas capturas partem do instantâneo, nunca de
uma nova execução do script.

Restauração antes do passo 3:

```bash
cp .refactor-arch/db.snapshot <arquivo>.db
```

Encerramento:

```bash
pkill -f "app.py"
```

### Node.js com Express

```bash
npm ci --silent          # quando houver arquivo de trava
npm start > .refactor-arch/boot.log 2>&1 &
# aguardar com verificação de identidade, conforme o passo 1.4
```

Node não isola: `node_modules/` é escrito na árvore do projeto, e `npm ci`
**apaga o diretório antes de instalar**. Registrar o que a instalação criou ou
alterou e conferir que nenhum arquivo versionado mudou.

Sem arquivo de trava, usar a forma resolvedora (`npm install`) e registrar que o
conjunto instalado não é reprodutível. Trava fora de sincronia com o manifesto,
ou falha de compilação de dependência nativa, interrompe o protocolo e é
reportada com o log preservado.

Com banco em memória, não há arquivo para copiar. O estado inicial é recriado a
cada boot pela rotina de carga, o que já garante que as duas execuções partem de
dados idênticos, desde que a rotina use valores literais e não valores derivados
do instante de execução. Se a rotina usar o instante de execução, acrescentar as
chaves afetadas à lista de voláteis do comparador.

Encerramento:

```bash
pkill -f "node src/app.js"
```

## Critério de aprovação

Os cinco itens do bloco `## Validação` da Fase 3 são preenchidos assim. Cada um
é resultado de execução: nenhum é preenchido por afirmação.

| Item | Aprovado quando |
|---|---|
| `A aplicação sobe sem erros` | O comando documentado sobe o processo e a identidade do servidor é confirmada conforme o passo 1.4 |
| `As <N> rotas respondem como na linha de base` | `compare.py` sai com código 0, com `--expected` quando houver correção autorizada |
| `O registro fecha: <N> constatações, 0 sem destino` | As três identidades de reconciliação de `remediation-protocol.md` fecham |
| `A re-auditoria não encontra constatação em aberto sem destino` | As duas passagens do passo 3.5 aprovam: nenhuma linha `CORRIGIDA` com sinal ainda casando, e nenhuma ocorrência da varredura sem linha correspondente no registro |
| `O comando de boot documentado não mudou` | O comando do README e o campo de script do manifesto são idênticos aos originais, **e** todo outro comando da sequência documentada executa com código de saída 0, conforme o passo 6 do Passo 3. Projeto sem script auxiliar registra `nenhum` e aprova |

Qualquer item reprovado impede a declaração de conclusão. O bloco é impresso com
`[FALHA]` no item correspondente e o laço de correção recomeça.

Constatação com destino `NÃO APLICADA` ou `MITIGADA` não reprova a
re-auditoria: ela aparece, respectivamente, em `## Não aplicadas` e em
`## Risco residual`. O que reprova é ocorrência sem destino declarado.

## Laço de correção

```
executar compare.py
      |
      +-- codigo 0 --> seguir para o passo 3.5 e fechar o registro
      |
      +-- codigo 1 --> ler cada divergencia
                       corrigir a causa no codigo refatorado
                       restaurar db.snapshot
                       repetir o passo 3
```

Não ajustar `requests.tsv` nem acrescentar chave volátil para fazer a comparação
passar. A divergência aponta uma mudança de comportamento e a correção é no
código.

Exceção única: divergência causada por correção autorizada no portão da Fase 2.
Nesse caso a divergência é declarada em `.refactor-arch/expected.json`, no passo
3.2, antes de aplicar, e o comparador é chamado com `--expected`. Declarar a
divergência depois de a validação reprovar, para fazê-la passar, inverte a
finalidade do arquivo: a declaração é derivada do campo `Mudança de contrato:`
da constatação autorizada, não do resultado observado.

## Falhas frequentes

| Sintoma | Causa | Correção |
|---|---|---|
| `status 000` em todas as entradas | Aplicação não subiu ou porta diferente | Conferir o log do processo e a porta configurada |
| Todas as entradas com o mesmo status e corpo vazio | Outro servidor ocupa a porta | Executar o passo 1.2 e encerrar o ocupante |
| Log do boot com `Address already in use` mas a captura concluiu | Outro servidor respondeu no lugar da aplicação | Executar o passo 1.2; em macOS, desativar o receptor AirPlay |
| Espera de identidade estoura o tempo com a aplicação respondendo 200 | Marcador com caractere não-ASCII, escapado pelo serializador JSON | Trocar por marcador ASCII, conforme o passo 1.4 |
| Cópia do banco falha com arquivo inexistente | Cópia feita antes de a aplicação criar o esquema | Copiar somente após a confirmação de identidade |
| Segunda captura reflete o código antigo | Processo filho do recarregador sobreviveu | Encerrar pelo padrão de linha de comando, conforme o passo 1.7 |
| Comparação aprova apesar de a regra de negócio ter mudado | Endpoint calculado sondado com o banco sem dados | Aplicar a cobertura de regras de negócio do passo 1.1 |
| `command not found: tail` a partir da primeira iteração | Variável `path` atribuída em zsh, que substitui o `PATH` | Usar `req_path`, conforme o passo 1.5 |
| Captura aborta com `read-only variable: status` | `status` é somente-leitura em zsh | Usar `http_status`, conforme o passo 1.5 |
| Divergência em toda chave de data | Banco recriado entre as execuções | Restaurar `db.snapshot` antes do passo 3 |
| Divergência apenas nos identificadores criados | Contadores partiram de valores diferentes | Restaurar `db.snapshot` antes do passo 3 |
| Divergência no tamanho de todas as listas | Escrita da execução anterior permaneceu | Restaurar `db.snapshot` antes do passo 3 |
| `ModuleNotFoundError` após a refatoração | Pacote sem arquivo de inicialização, ou raiz de importação diferente | Criar o arquivo de pacote; conferir de onde o processo é iniciado |
| Duas execuções concordam, mas o valor é montado por ordem de conclusão | Callback, thread ou consulta sem `ORDER BY`: a ordem não é contrato | Registrar em `runtime.md` como resposta derivada de ordem e reexaminar a divergência de ordenação no passo 4 antes de tratá-la como regressão |
| Captura inteira com status `000` e a aplicação sadia | `BASE_URL` usou `localhost`, resolvido para `::1`, com o processo escutando em IPv4 | Usar o literal de loopback, conforme o passo 1.0 |
| Aplicação sobe, endpoint devolve 404 | Rota não registrada na camada de rotas | Comparar com o inventário da Fase 1 |
| Aplicação não sobe, arquivo de entrada não encontrado | Ponto de entrada movido | Ver `mvc-architecture.md`, "Preservação do ponto de entrada" |
| Divergência exatamente onde a correção autorizada agiu | Falta a entrada em `expected.json` | Declarar a mudança a partir do campo `Mudança de contrato:` e repetir o passo 3.4 |
| `autorizada e não observada` para uma constatação | A correção foi autorizada no portão e não foi aplicada | Aplicar a correção; não remover a entrada do arquivo |
| Comparação aprova, mas o registro tem linha sem destino | Reconciliação do passo 3.5 não executada | Executar as três identidades de `remediation-protocol.md` |
| Stack sem receita neste arquivo | Projeto fora das duas stacks exemplificadas | Preencher os seis parâmetros do procedimento genérico com fatos da Fase 1 |
| `lsof` ou `pkill` indisponíveis | Ambiente não POSIX | Usar o substituto da tabela "Ferramentas de apoio" e registrar a substituição |
