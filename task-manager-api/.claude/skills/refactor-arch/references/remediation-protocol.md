# Protocolo de remediação: identidade, autorização, destino e fechamento

## Conteúdo

- Objetivo
- Idioma da saída
- Identidade da constatação
- Localizações de uma constatação
- Autorização no portão
- Reclassificação depois do portão
- Vocabulário de destino
- O registro de remediação
- Reconciliação aritmética
- Mudanças esperadas e o arquivo `expected.json`
- Re-auditoria de fechamento
- Critério de conclusão

## Objetivo

Garantir que toda constatação emitida na Fase 2 tenha, ao final da Fase 3, um
destino declarado, verificado e impresso.

O protocolo existe porque a ausência dele é silenciosa. Uma constatação que
ninguém corrige e ninguém menciona desaparece sem produzir erro algum: o
relatório continua correto, a validação continua aprovando e o bloco final
continua sendo impresso. Nada falha.

Este arquivo define o que torna esse desaparecimento impossível: um
identificador estável por constatação, um registro com uma linha por
localização, uma conta que precisa fechar, e uma re-auditoria que confirma no
código o que o registro afirma.

## Idioma da saída

Todo texto corrido que a pessoa que executa a skill lê é escrito em português:
os blocos impressos das Fases 1 e 3, o texto do portão, os arquivos de trabalho
em `.refactor-arch/`, as mensagens do comparador e o conteúdo de cada campo do
relatório de auditoria.

Escrever em português claro e objetivo. Frases curtas, voz ativa, uma afirmação
por frase. Descrever consequência verificável em vez de julgamento. Não usar
emoji, ícone, sinal decorativo nem marcador gráfico em nenhuma saída: o estado
de um item de validação é escrito como `[OK]` ou `[FALHA]`.

Quatro categorias permanecem em inglês, porque são chave e não texto corrido:

| Categoria | Exemplos | Por que |
|---|---|---|
| Escala de severidade | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` | é a escala definida pelo enunciado do desafio e usada como critério de aceite |
| Rótulos de estrutura do relatório de auditoria | `ARCHITECTURE AUDIT REPORT`, `Project:`, `Stack:`, `Files:`, `## Summary`, `## Findings`, `File:`, `Locations:`, `Description:`, `Impact:`, `Recommendation:`, `Contract change:`, `[contract-breaking]`, `Total: <N> findings` | é o formato de saída fixado pelo enunciado do desafio; a lista completa está em `audit-report-template.md` |
| Identificadores | `C1`, `H3`, `M5`, `T1`, `T23`, `F01` | são chaves de referência cruzada entre arquivos, não prose |
| Interface de programa | nomes de arquivo em `.refactor-arch/`, chaves de `expected.json`, a opção `--expected` | são consumidos por script, não lidos como texto |

O conteúdo dentro dessas estruturas continua em português. Rótulo em inglês,
conteúdo em português: um título de constatação, uma descrição, um impacto, uma
recomendação e uma mudança de contrato são sempre escritos em português, mesmo
que o rótulo acima deles seja inglês.

A segunda categoria vale apenas para o relatório de auditoria. Os blocos
impressos das Fases 1 e 3 e o texto do portão mantêm os rótulos em português
definidos em `SKILL.md`.

## Identidade da constatação

O identificador do catálogo não identifica uma constatação. Ele identifica a
entrada do catálogo, e a mesma entrada aparece várias vezes em um relatório:
dois arquivos com senha em texto puro são duas constatações `C5`, e uma
auditoria real chegou a repetir `C5`, `C6`, `M5`, `L2` e `L3`.

Sem chave única não existe lista de portão confiável, nem registro, nem
re-auditoria dirigida.

Cada constatação recebe, no passo 2.4, um identificador próprio: `F01`, `F02`,
`F03`, e assim por diante.

Regras:

1. Numeração sequencial na ordem final do relatório, começando em `F01`.
2. O identificador é atribuído uma vez e nunca muda. Ele é a chave usada pelo
   portão, pelo registro de remediação, pelo `expected.json`, pela re-auditoria
   e pelo bloco da Fase 3.
3. O identificador do catálogo continua no título, ao lado do `F`. Os dois
   convivem e têm papéis diferentes: `F07` é a constatação, `C6` é o padrão que
   ela instancia.
4. Duas constatações nunca compartilham o mesmo `F`. Se a auditoria for
   refeita, a numeração é refeita junto e o relatório anterior é substituído
   por inteiro.

## Localizações de uma constatação

Uma constatação pode ocorrer em mais de um lugar. Corrigir um lugar e declarar
a constatação resolvida é a forma mais comum de correção parcial.

O caso observado: uma chave secreta embutida no código foi corrigida no módulo
de configuração, mas o mesmo literal continuava em um controlador que o
devolvia na resposta de verificação de saúde. A constatação citava as duas
localizações no texto da descrição; o campo `File:` citava só a primeira; a
transformação tratou só a primeira.

Por isso toda constatação declara suas localizações de forma enumerável:

```
File: src/config/settings.py:13
Locations: src/config/settings.py:13, src/controllers/health_controller.py:24
```

- `File:` é a localização principal, para leitura humana.
- `Locations:` lista todas, inclusive a principal. O campo só é escrito
  quando a constatação alcança mais de um arquivo. Quando há um só arquivo,
  `File:` já basta, inclusive na forma `arquivo.py:12,28,45`.
- O registro de remediação abre uma linha por localização. Uma constatação com
  três localizações fecha somente quando as três fecham.
- Localização descoberta durante a Fase 3 é acrescentada à constatação
  existente e ganha linha no registro. Ela não vira constatação nova.

## Autorização no portão

O portão da Fase 2 decide o conjunto autorizado. É a única oportunidade de
decisão da pessoa que executa a skill, então precisa apresentar as opções e o
custo de cada uma.

O portão apresenta quatro opções:

| Resposta | Significado |
|---|---|
| `a` | aplicar todas as correções, inclusive as que alteram o contrato |
| `s` | aplicar somente as correções que preservam o contrato |
| números | aplicar as que preservam o contrato mais os itens listados |
| `n` | não alterar nada e encerrar |

Regras:

1. O portão informa, em cada opção, quantas constatações e de que severidade
   permanecem no código se aquela opção for escolhida. O custo de declinar é
   explícito, não implícito.
2. Resposta afirmativa que não seleciona uma opção não é seleção. `sim`, `ok`,
   `pode`, `y` são ambíguos: cabem tanto em `a` quanto em `s`. Nesse caso,
   perguntar uma única vez de novo, apresentando em uma linha a consequência de
   `a` e a consequência de `s`. Não escolher pela pessoa e não adotar o mínimo
   por omissão.
3. O conjunto autorizado é gravado em `.refactor-arch/authorization.md` no
   início da Fase 3, com a resposta literal recebida e a lista de `F`
   autorizados. Nenhum passo posterior pode reduzir esse conjunto.
4. Correções que preservam o contrato não dependem de seleção: entram no
   conjunto autorizado em qualquer resposta diferente de `n`.
5. **Transformação com mais de uma opção.** Quando a transformação nomeada em
   `Recommendation:` oferece opções, o playbook declara qual é a recomendada, e o
   item do portão a nomeia no texto. Um número nu seleciona a opção recomendada;
   as formas `<n>a` e `<n>b` selecionam explicitamente. No máximo duas opções
   por item. Sufixo não reconhecido é resposta ambígua e vai para a mesma
   pergunta única de desambiguação da regra 2, nunca truncado em silêncio para o
   número nu.
6. **Constatação que terminará `MITIGADA` é anunciada no portão.** Quando o
   padrão prescrito pela transformação preserva a condição insegura descrita na
   constatação, isso é dito antes da resposta, no bloco `RISCO RESIDUAL
   PREVISTO`, com o que permanece e o que fecha. Quando adotar o padrão
   restritivo é opção real, a constatação também aparece na listagem numerada
   como item que altera o contrato.

   O princípio: `MITIGADA` é destino legítimo, mas escolhê-lo é decisão de quem
   executa. Apresentá-lo apenas no relatório final é apresentá-lo depois de
   tomado.

## Reclassificação depois do portão

Descobrir, durante a Fase 3, que uma correção classificada como preservadora do
contrato na verdade o altera é possível e legítimo. Resolver isso sozinho não é.

O caso observado: uma constatação de validação de entrada incompleta foi
reclassificada dentro do plano da Fase 3 e descartada com a justificativa da
própria reclassificação. A pessoa que autorizou a refatoração nunca soube.

Procedimento correto:

1. Parar a transformação.
2. Registrar a reclassificação no registro de remediação, com o motivo.
3. Voltar com um portão estreito, listando apenas os itens reclassificados e o
   que muda em cada um.
4. Prosseguir conforme a resposta recebida.

Uma reclassificação nunca produz, por si só, o destino `NÃO APLICADA`. Somente
a resposta da pessoa produz.

## Vocabulário de destino

Toda constatação termina em exatamente um destes destinos.

| Destino | Significado | Evidência exigida |
|---|---|---|
| `CORRIGIDA` | o sinal de detecção não casa mais em nenhuma localização, e a verificação da transformação foi executada e passou | localização nova de cada trecho e o resultado da verificação |
| `MITIGADA` | a estrutura mudou, mas a condição observável descrita na constatação permanece, por decisão registrada | o que permanece, por quê, e o que fecha |
| `NÃO APLICADA` | a pessoa declinou a correção no portão | o item do portão e a resposta que o declinou |

Notas:

1. `MITIGADA` existe para o caso em que a transformação prescreve preservar o
   comportamento atual como padrão. Uma política de origem cruzada que passou a
   ser configurável mas continua aberta enquanto ninguém definir a variável é
   `MITIGADA`, não `CORRIGIDA`. Chamar isso de corrigido é o que faz um achado
   de segurança sair do relatório sem ter saído do código.

   `MITIGADA` não é alcançável sem que a pessoa tenha visto o residual no
   portão, conforme a regra 6 de "Autorização no portão". A exceção é o residual
   que só se revelou na Fase 3, e esse caso é reclassificação: segue o portão
   estreito.
2. `MITIGADA` conta como não corrigida no resumo de fechamento e aparece em
   `Risco residual`.
3. Não existe destino para "não deu tempo", "não era importante" ou
   "reclassificada". Linha sem destino reprova a Fase 3.
4. Constatação introduzida pela própria refatoração, encontrada na
   re-auditoria, não recebe destino: é regressão e precisa ser corrigida antes
   da conclusão. Não pode ser declinada, porque ninguém a viu no portão.

## O registro de remediação

Arquivo `.refactor-arch/ledger.md`, criado no passo 3.2 e preenchido ao longo
do 3.3. Uma linha por localização de constatação:

```
| F   | Sev      | Cat | Localização original      | T   | Destino      | Evidência                                                        |
|-----|----------|-----|---------------------------|-----|--------------|------------------------------------------------------------------|
| F01 | CRITICAL | C2  | app.py:7                  | T2  | CORRIGIDA    | src/config/settings.py:13; varredura do literal: 0 ocorrências    |
| F01 | CRITICAL | C2  | controllers.py:289        | T2  | CORRIGIDA    | chave removida de src/controllers/health_controller.py:24         |
| F12 | HIGH     | H8  | app.py:9                  | T19 | MITIGADA     | origens configuráveis; padrão continua aberto; fechar definindo CORS_ORIGINS |
| F04 | CRITICAL | C3  | app.py:59-78              | T16 | NÃO APLICADA | item [2] do portão; resposta selecionou `s`                       |
```

Regras:

1. O registro é semeado no passo 3.2 com todas as constatações do relatório,
   todas com destino em branco. Semear depois de aplicar não serve: o que se
   quer impedir é justamente esquecer de listar.
2. Uma linha só recebe destino depois que a evidência existe.
3. A coluna `Evidência` aponta arquivo e linha do código refatorado, ou o
   resultado do comando de verificação. Afirmação sem localização não é
   evidência.

## Reconciliação aritmética

Executada duas vezes: no passo 3.2, ao semear, e no passo 3.5, ao fechar.

```
linhas do registro      ==  soma das localizações de todas as constatações
constatações distintas  ==  o número em Total: do relatório
linhas sem destino      ==  0                      (somente no fechamento)
```

Qualquer identidade que não feche reprova a Fase 3. A conferência é aritmética,
não julgamento, e é isso que a torna difícil de contornar.

## Mudanças esperadas e o arquivo `expected.json`

Toda correção autorizada que altera o contrato HTTP produz divergência entre a
linha de base e a captura final. Sem declaração prévia, o comparador reprova
essa divergência, e a Fase 3 passa a ter um incentivo invertido: não aplicar a
correção é o caminho que passa na validação.

A declaração fica em `.refactor-arch/expected.json`, escrita no passo 3.2,
antes de aplicar, a partir do campo `Contract change:` de cada constatação
autorizada.

```json
[
  {"finding": "F07", "request": "GET /health",       "key": "body.secret_key",     "kind": "removida"},
  {"finding": "F09", "request": "GET /usuarios",     "key": "body.dados[*].senha", "kind": "removida"},
  {"finding": "F04", "request": "POST /admin/query", "key": "status",              "kind": "status"}
]
```

| Chave | Conteúdo |
|---|---|
| `finding` | o identificador `F` da constatação autorizada |
| `request` | `<MÉTODO> <caminho>` exatamente como aparece na captura |
| `key` | caminho da chave dentro da resposta, ou `status`; `*` é o único curinga |
| `kind` | opcional; restringe o tipo: `removida`, `acrescentada`, `valor`, `tipo`, `status`, `tamanho` |

O comparador usa o arquivo nos dois sentidos:

- divergência declarada e observada: autorizada, não reprova;
- divergência não declarada: reprova;
- divergência declarada e não observada: reprova.

O terceiro caso é o que fecha a porta que deixou seis correções autorizadas por
aplicar em uma execução real. Se a correção foi autorizada no portão e não
produziu a mudança prometida, ela não foi aplicada, e a validação passa a dizer
isso em vez de aprovar.

### Correção autorizada que não é observável por HTTP

Algumas correções autorizadas não aparecem na captura. Trocar o armazenamento
de senha por digest com sal não muda resposta alguma quando o endpoint que
expunha a senha também foi corrigido.

Nesse caso a entrada se declara não observável e carrega a verificação que a
substitui:

```json
{"finding": "F11", "observable": false,
 "verification": "grep -c 'pbkdf2_' no artefato de carga inicial: 3 de 3 usuários"}
```

O comparador ignora entradas não observáveis. O registro de remediação não
ignora: a verificação declarada precisa ter sido executada e o resultado
precisa estar na coluna `Evidência`.

Toda constatação autorizada tem entrada em `expected.json`, observável ou não.
Constatação autorizada sem entrada é falha do passo 3.2.

## Re-auditoria de fechamento

Executada no passo 3.5, sobre o código refatorado, depois de a comparação
aprovar. Duas passagens, ambas obrigatórias.

### Passagem A, dirigida

Para cada linha do registro, buscar o sinal de detecção do catálogo na
localização declarada e no trecho equivalente do código novo.

| Destino da linha | Resultado que aprova |
|---|---|
| `CORRIGIDA` | o sinal não casa |
| `MITIGADA` | o sinal casa, e o que casa é exatamente o residual declarado |
| `NÃO APLICADA` | o sinal casa, e a constatação consta como declinada na autorização |

Sinal que ainda casa em linha marcada `CORRIGIDA` reprova a Fase 3.

### Passagem B, varredura

Reexecutar os passos 2.1, 2.2 e 2.3 inteiros sobre o código refatorado, como se
fosse a primeira auditoria do projeto.

A varredura corre sobre o **escopo de código-fonte do projeto** definido em
`stack-detection.md`. Sem esse recorte, a passagem B reencontra todo literal de
exemplo que a própria skill traz em `references/` e todo trecho citado em
`reports/`, e quem lê aprende a desconsiderar o resultado. É o mesmo efeito que
inutiliza uma varredura de resíduo sem escopo.

Toda ocorrência encontrada precisa mapear para uma linha do registro. O que não
mapear é regressão introduzida pela refatoração: entra como constatação nova e
precisa ser corrigida antes da conclusão.

A passagem B é o que impede a re-auditoria de virar autoconfirmação. A passagem
A procura o que espera encontrar; a passagem B olha o código sem expectativa.

## Critério de conclusão

A Fase 3 só é declarada concluída quando os seis itens aprovam:

| Item | Aprovado quando |
|---|---|
| Boot | o comando documentado sobe o processo e a identidade do servidor é confirmada |
| Contrato | `compare.py` sai com código 0, usando `--expected` quando houver correção autorizada |
| Reconciliação | as três identidades fecham e nenhuma linha ficou sem destino |
| Re-auditoria dirigida | nenhuma linha `CORRIGIDA` com sinal ainda casando |
| Re-auditoria por varredura | nenhuma ocorrência sem linha correspondente no registro |
| Sequência documentada de execução | o comando de boot é idêntico ao original e todo outro comando da sequência documentada executa com código de saída 0 |

Item reprovado impede a conclusão. Não existe conclusão parcial: o bloco da
Fase 3 é impresso com `[FALHA]` no item correspondente, e o laço de correção
recomeça.
