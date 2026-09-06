---
name: refactor-arch
description: Analisa uma codebase, audita anti-patterns e violações de MVC e SOLID com arquivo e linha exatos, e refatora o projeto para o padrão Model-View-Controller preservando o contrato HTTP existente. Detecta linguagem, framework, banco de dados e arquitetura atual sem configuração prévia, e valida o resultado subindo a aplicação e reexercitando os endpoints. Use quando o pedido envolver análise de arquitetura, architecture audit, auditoria de code smells, relatório de severidade CRITICAL/HIGH/MEDIUM/LOW, detecção de APIs obsoletas, separação de camadas, violação de SOLID, ou refatoração para MVC em projetos Python/Flask, Node.js/Express ou outras stacks de backend.
disable-model-invocation: true
---

# refactor-arch

Executa três fases sequenciais sobre o projeto no diretório de trabalho atual:
análise, auditoria e refatoração para o padrão Model-View-Controller.

A skill é agnóstica de stack. Toda decisão específica de linguagem ou framework
vem dos arquivos de referência, nunca de suposição.

## Regras permanentes

Estas regras valem durante toda a execução, não apenas no passo em que aparecem.

1. Executar as fases na ordem 1, 2, 3. Não pular nem fundir fases.
2. Toda constatação da Fase 2 exige caminho de arquivo e intervalo de linhas
   confirmados por leitura do próprio arquivo. Constatação sem localização
   confirmada não entra no relatório.
3. Não usar `Edit`, `Write`, `NotebookEdit`, nem comando de shell que grave,
   mova ou apague arquivo antes de o usuário responder afirmativamente ao
   portão da Fase 2. Única exceção: criar o arquivo novo
   `reports/audit-<slug>.md` no passo 2.4.
4. O contrato HTTP é invariante. Caminho da rota, método, código de status de
   sucesso e chaves do corpo de resposta não mudam.
5. Regras de negócio observáveis são invariantes. Nenhuma fórmula, faixa,
   limite, prefixo ou lista de valores válidos é alterada.
6. O comando de boot documentado no projeto continua funcionando após a Fase 3,
   com o mesmo nome de arquivo de entrada.
7. Não introduzir dependência nova. Refatorar apenas com o que o projeto já
   declara no seu arquivo de dependências e com a biblioteca padrão da
   linguagem. A tabela de manifestos de `references/stack-detection.md` é o
   único lugar que nomeia arquivos de dependência por stack.
8. Correções que quebram o item 4 ou o item 5 alteram o contrato, entram no
   relatório com a marca correspondente e só são aplicadas se o usuário
   autorizar no portão da Fase 2.
9. Não inferir. Se um dado não puder ser lido do projeto ou de uma referência
   desta skill, registrar `desconhecido` em vez de estimar.
10. Toda constatação recebe um identificador próprio `F<NN>` no passo 2.4 e
    termina a Fase 3 com um destino declarado, verificado e impresso.
    Constatação sem destino reprova a Fase 3. Ver
    `references/remediation-protocol.md`.
11. O conjunto autorizado no portão não pode ser reduzido depois. Descobrir na
    Fase 3 que uma correção altera o contrato não autoriza descartá-la: o
    procedimento é voltar ao usuário com um portão estreito.
12. Concluir a Fase 3 exige re-auditoria sobre o código refatorado. Os itens do
    bloco `## Validação` são resultado de execução, nunca de afirmação.
13. Toda saída lida pelo usuário é escrita em português claro e objetivo, sem
    emoji e sem sinal decorativo. Permanecem em inglês apenas a escala de
    severidade e os identificadores, conforme a seção "Idioma da saída" de
    `references/remediation-protocol.md`.

## Arquivos de referência

Carregar cada arquivo no momento indicado, não antes.

| Arquivo | Quando ler |
|---|---|
| [references/stack-detection.md](references/stack-detection.md) | Antes da Fase 1 |
| [references/mvc-architecture.md](references/mvc-architecture.md) | Antes da Fase 1; a tabela `contém / não contém` é usada nos passos 1.2, 2.2 e 3.2 |
| [references/antipattern-catalog.md](references/antipattern-catalog.md) | Antes da Fase 2 |
| [references/solid-principles.md](references/solid-principles.md) | Antes da Fase 2 |
| [references/deprecated-apis.md](references/deprecated-apis.md) | Antes da Fase 2 |
| [references/remediation-protocol.md](references/remediation-protocol.md) | Antes do passo 2.4; usado em 2.4, 2.5, 3.1, 3.2, 3.3, 3.5 e 3.6 |
| [references/audit-report-template.md](references/audit-report-template.md) | No passo 2.4 |
| [references/refactoring-playbook.md](references/refactoring-playbook.md) | Antes da Fase 3 |
| [references/validation-protocol.md](references/validation-protocol.md) | No passo 3.1 |

A skill também traz `scripts/compare.py`. Esse arquivo é executado, não lido: no
passo 3.4, rodar
`python3 "${CLAUDE_SKILL_DIR}/scripts/compare.py" .refactor-arch/baseline.json .refactor-arch/after.json`,
acrescentando `--expected .refactor-arch/expected.json` quando houver correção
autorizada que altere o contrato. Não reescrever nem copiar o script. Ao levar a
skill para outro projeto, copiar o diretório `refactor-arch/` inteiro, incluindo
`scripts/`.

## Checklist de progresso

Copiar este bloco para a resposta e marcar cada item ao concluí-lo.

```
Progresso refactor-arch:
- [ ] 1.1 Detectar linguagem, framework, dependências e banco
- [ ] 1.2 Mapear arquitetura atual e classificar o nível de separação
- [ ] 1.3 Inventariar rotas, arquivos-fonte e linhas
- [ ] 1.4 Imprimir o bloco da Fase 1
- [ ] 2.1 Cruzar o código contra o catálogo de anti-patterns
- [ ] 2.2 Cruzar o código contra MVC e SOLID
- [ ] 2.3 Cruzar o código contra a tabela de APIs obsoletas
- [ ] 2.4 Numerar as constatações e gravar o relatório de auditoria
- [ ] 2.5 Pausar no portão de confirmação
- [ ] 3.1 Registrar a autorização e capturar a linha de base
- [ ] 3.2 Escrever o plano, semear o registro e declarar as mudanças esperadas
- [ ] 3.3 Aplicar as transformações e preencher os destinos
- [ ] 3.4 Revalidar e comparar com a linha de base
- [ ] 3.5 Re-auditar o código refatorado e reconciliar o registro
- [ ] 3.6 Imprimir o bloco da Fase 3
```

---

## Fase 1 — Análise

Ler `references/stack-detection.md` e `references/mvc-architecture.md` antes de
começar. O passo 1.2 usa a tabela `contém / não contém` do segundo arquivo.

**1.1 Detectar a stack.** Aplicar a tabela de sinais na ordem de precedência
definida na referência. Extrair a versão do framework do arquivo de
dependências, não do código. Listar as demais dependências declaradas.
Identificar o banco a partir da chamada de conexão e as tabelas a partir dos
comandos de criação de esquema ou das declarações de modelo.

**1.2 Mapear a arquitetura atual.** Listar os diretórios de código. Classificar
em `sem camadas`, `camadas parciais` ou `camadas completas` conforme o
procedimento da referência. Registrar quais responsabilidades estão fora da
camada correta.

**1.3 Inventariar.** Contar arquivos-fonte e linhas. Extrair todas as rotas com
caminho e método. Esse inventário é o contrato que a Fase 3 deve preservar.

**1.4 Imprimir o bloco.** Formato fixo, exatamente com estes rótulos e nesta
ordem:

```
================================
FASE 1: ANÁLISE DO PROJETO
================================
Linguagem:        <linguagem>
Framework:        <framework e versão declarada>
Dependências:     <lista separada por vírgula>
Domínio:          <domínio derivado das tabelas e rotas>
Arquitetura:      <classificação e evidência em uma linha>
Arquivos-fonte:   <N> arquivos analisados
Tabelas do banco: <lista separada por vírgula>
Ponto de entrada: <arquivo> (<comando de boot documentado>)
Rotas:            <N> endpoints
Linhas de código: <N>
================================
```

Campo sem evidência recebe `desconhecido`. Não estimar.

---

## Fase 2 — Auditoria

Ler `references/antipattern-catalog.md`, `references/solid-principles.md`,
`references/deprecated-apis.md` e `references/remediation-protocol.md` antes de
começar. `references/mvc-architecture.md` já foi carregado na Fase 1 e é usado
no passo 2.2.

**2.1 Cruzar contra o catálogo.** Para cada entrada do catálogo, buscar o sinal
de detecção no código. Para cada ocorrência encontrada, abrir o arquivo e
confirmar o intervalo de linhas. Registrar o identificador da entrada.

**2.2 Cruzar contra MVC e SOLID.** Aplicar a tabela `contém / não contém` de
`references/mvc-architecture.md` a cada arquivo e os cinco sinais de detecção de
`references/solid-principles.md`. Violações de camada e de princípio entram no
relatório com a mesma estrutura das demais constatações.

**2.3 Cruzar contra APIs obsoletas.** Resolver cada símbolo obsoleto contra a
versão declarada da dependência, conforme o procedimento da referência. Reportar
sempre com o substituto oficial nomeado.

**2.4 Numerar e emitir o relatório.** Ordenar as constatações por severidade
decrescente: CRITICAL, HIGH, MEDIUM, LOW. Dentro da mesma severidade, ordenar
por caminho de arquivo. Só então numerar de `F01` em diante, na ordem final.

Registrar em `Localizações:` todas as localizações de cada constatação que
alcance mais de um arquivo. É esse campo que impede a correção parcial na Fase
3. Usar o template de `references/audit-report-template.md` sem alterar a
estrutura.

Gravar em `reports/audit-<slug>.md`, onde `<slug>` é o nome do diretório raiz do
projeto, e imprimir o mesmo conteúdo na resposta. Este é o único arquivo que
pode ser criado antes do portão.

Uma constatação altera o contrato quando a correção muda chave de resposta,
remove endpoint, altera texto de resposta, invalida dado já persistido, ou muda
o estado do banco resultante de uma operação. Ela recebe a marca
`[altera-contrato]` no título e o campo `Mudança de contrato:`, e permanece
ordenada pela própria severidade dentro de `## Constatações`. Não criar bloco
separado dentro do relatório: a listagem numerada dessas constatações é o bloco
impresso no passo 2.5, depois do rodapé `Total:` e fora do relatório.

Decidir aqui, e não na Fase 3, se uma correção altera o contrato. Uma validação
de entrada que passará a recusar dado hoje aceito e persistido altera o
contrato e precisa constar do portão. Adiar essa decisão para a Fase 3 é o que
faz uma constatação ser descartada sem que o usuário saiba.

**2.5 Pausar.** Encerrar o turno com este texto e não executar mais nada:

```
================================
Total: <N> constatações
================================

CORREÇÕES QUE ALTERAM O CONTRATO (autorização em separado)
  [1] <F> <título curto> - <o que muda>
  [2] ...

RISCO RESIDUAL PREVISTO (a correção padrão não fecha a constatação)
  <F> <título curto> - <o que permanece> - fecha com <o que fecha>

Fase 2 concluída. Como a Fase 3 deve prosseguir?
  [a]        aplicar todas as <N> correções, inclusive as <K> que alteram o contrato
  [s]        aplicar somente as <N-K> que preservam o contrato
             deixa <K> constatações no código: <x> CRITICAL, <y> HIGH, <z> MEDIUM, <w> LOW
  [1 3 ...]  aplicar as que preservam o contrato mais os itens listados acima
  [n]        não alterar nada e encerrar

Responda com uma das opções.
```

O bloco `RISCO RESIDUAL PREVISTO` lista as constatações cuja transformação
padrão preserva a condição insegura e que, por isso, terminarão `MITIGADA`.
Omitir o bloco quando não houver nenhuma. Anunciá-las aqui, e não apenas no
bloco da Fase 3, é o que permite ao usuário decidir: apresentá-las só no
relatório final é apresentá-las depois da decisão tomada.

Item cuja transformação oferece opções é selecionado pelo número nu, que escolhe
a opção recomendada nomeada no texto do item, ou pelas formas `<n>a` e `<n>b`,
conforme `references/remediation-protocol.md`, "Autorização no portão".

Se não houver constatação que altere o contrato, omitir os blocos de listagem e
as opções, e manter apenas:

```
Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n]
```

Resposta afirmativa que não seleciona uma das opções não é seleção. `sim`, `ok`,
`pode` e `y` cabem tanto em `a` quanto em `s`. Nesse caso, perguntar uma única
vez de novo, apresentando em uma linha a consequência de `a` e a de `s`. Não
escolher pelo usuário e não adotar o mínimo por omissão.

Resposta `n`, ou qualquer resposta não afirmativa, encerra a execução sem
alterar arquivo.

---

## Fase 3 — Refatoração

Executar somente após resposta afirmativa. Ler
`references/mvc-architecture.md`, `references/refactoring-playbook.md` e
`references/validation-protocol.md` antes de começar.
`references/remediation-protocol.md` já foi carregado na Fase 2.

**3.1 Registrar a autorização e capturar a linha de base.** Gravar
`.refactor-arch/authorization.md` com a resposta literal recebida e a lista de
`F` autorizados. Em seguida, seguir o passo 1 de
`references/validation-protocol.md`. A captura acontece antes da primeira
edição, com o código ainda original. Sem linha de base gravada, não prosseguir.

**3.2 Escrever o plano, semear o registro e declarar as mudanças esperadas.**
Antes de editar, produzir três arquivos.

Em `.refactor-arch/plan.md`:

- a árvore de diretórios alvo, derivada de `references/mvc-architecture.md`;
- a lista `arquivo de origem -> arquivo de destino` para cada bloco de código
  movido;
- a lista de transformações do playbook a aplicar, por identificador;
- o inventário de rotas da Fase 1, que serve de critério de aceite;
- a lista de correções autorizadas no portão, ou `nenhuma`.

Em `.refactor-arch/ledger.md`, o registro de remediação: uma linha por
localização de cada constatação do relatório, com o destino em branco. Semear
depois de aplicar não serve, porque o que se quer impedir é justamente esquecer
de listar.

Em `.refactor-arch/expected.json`: uma entrada por constatação autorizada que
altere o contrato, traduzida do campo `Mudança de contrato:`.

Conferir as três identidades de reconciliação e as regras permanentes 4 a 8
antes de aplicar.

**3.3 Aplicar.** Executar as transformações na ordem do playbook. Uma
transformação por vez. Não misturar movimentação de arquivo com mudança de
lógica no mesmo passo. Ao concluir cada transformação, executar a verificação
indicada por ela e preencher destino e evidência nas linhas correspondentes do
registro.

**3.4 Revalidar.** Seguir os passos 3 e 4 de
`references/validation-protocol.md`, usando `--expected` quando houver correção
autorizada. Divergência não autorizada reprova. Divergência autorizada que não
ocorreu também reprova: significa que a correção autorizada não foi aplicada.
Em caso de reprovação, corrigir e repetir o passo 3.4.

**3.5 Re-auditar e reconciliar.** Executar as duas passagens de
`references/remediation-protocol.md`: a dirigida, linha a linha do registro, e a
varredura completa dos passos 2.1, 2.2 e 2.3 sobre o código refatorado.
Conferir as três identidades de reconciliação. Regressão introduzida pela
refatoração é corrigida antes da conclusão, não declinada.

**3.6 Imprimir o bloco.** Formato fixo:

```
================================
FASE 3: REFATORAÇÃO CONCLUÍDA
================================
## Nova estrutura do projeto
<árvore de diretórios resultante>

## Transformações aplicadas
  <id> <nome> - <N> ocorrências

## Remediação
  Constatações relatadas: <N>
  Corrigidas:             <N>
  Mitigadas:              <N>
  Não aplicadas:          <N>
  Sem destino:            0

  <F> [<severidade>] <título curto> - <destino>
  ...

## Validação
  [OK|FALHA] A aplicação sobe sem erros
  [OK|FALHA] As <N> rotas respondem como na linha de base
  [OK|FALHA] O registro fecha: <N> constatações, 0 sem destino
  [OK|FALHA] A re-auditoria não encontra constatação em aberto sem destino
  [OK|FALHA] O comando de boot documentado não mudou

## Risco residual
  <F> <título> - <o que permanece e o que fecha>

## Não aplicadas
  <F> <título> - declinada no portão, item [<n>]
================================
```

`Risco residual` lista as constatações com destino `MITIGADA`. `Não aplicadas`
lista as declinadas no portão. Quando uma das listas estiver vazia, escrever
`nenhuma`. `Sem destino` diferente de zero reprova a fase.

---

## Erros comuns

**A Fase 2 encontrou menos de cinco constatações.** O catálogo foi aplicado
parcialmente. Reexecutar o passo 2.1 percorrendo todas as entradas do catálogo,
incluindo as de severidade LOW, e o passo 2.2 sobre todos os arquivos.

**O usuário respondeu apenas `sim` no portão.** Isso não seleciona entre `a` e
`s`. Perguntar de novo uma única vez, com as duas consequências. Não adotar o
mínimo por omissão. Ver `references/remediation-protocol.md`, "Autorização no
portão".

**Uma correção mostrou-se alteradora do contrato só na Fase 3.** Parar, registrar a
reclassificação e voltar ao usuário com um portão estreito. Descartar a
correção com base na própria reclassificação é o erro que a regra permanente 11
proíbe.

**A validação reprovou justamente onde a correção autorizada agiu.** Falta a
entrada correspondente em `.refactor-arch/expected.json`. Declarar a mudança e
repetir o passo 3.4.

**A validação acusou `autorizada e não observada`.** A correção foi autorizada
no portão e não produziu a mudança declarada. Aplicá-la; não remover a entrada
do arquivo de mudanças esperadas.

**Uma constatação sumiu entre o relatório e o bloco final.** A reconciliação do
passo 3.5 não foi executada, ou o registro foi semeado depois de aplicar. O
registro é semeado no passo 3.2, com todas as constatações e destino em branco.

**A aplicação não sobe após a Fase 3.** Causa mais frequente: o arquivo de
entrada mudou de caminho e o comando documentado deixou de encontrá-lo. Ver
`references/mvc-architecture.md`, seção "Preservação do ponto de entrada".

**Um endpoint mudou o corpo da resposta.** Comparar com
`.refactor-arch/baseline.json` e restaurar a chave removida. Remoção de chave só
é permitida se constava como autorizada no portão e declarada em
`expected.json`.

**A validação não roda por falta de dependência.** Instalar a partir do arquivo
de dependências já declarado no projeto, em ambiente isolado. Não adicionar
dependência ao projeto para viabilizar a validação.

**A captura concluiu, mas todas as respostas têm o mesmo status.** Outro
servidor ocupa a porta e respondeu no lugar da aplicação. Ver
`references/validation-protocol.md`, passos 1.2 e 1.4.

**A validação aprovou, mas uma regra de negócio mudou.** O conjunto de
requisições exercitou a rota sem exercitar o ramo do cálculo. Ver
`references/validation-protocol.md`, passo 1.1, cobertura de regras de negócio.

**A stack do projeto não está nas tabelas das referências.** Preencher os
parâmetros do procedimento genérico com fatos lidos na Fase 1. Ver
`references/validation-protocol.md`, "Procedimento genérico, para qualquer
stack".
