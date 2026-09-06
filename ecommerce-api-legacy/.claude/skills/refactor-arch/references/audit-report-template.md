# Template do relatório de auditoria

## Conteúdo

- Regras de preenchimento
- Estrutura obrigatória
- Ordenação
- Exemplo preenchido
- Erros de preenchimento

## Regras de preenchimento

Usar esta estrutura sem alterá-la. Não acrescentar, remover nem renomear seção.

1. O relatório é escrito em português, inclusive os rótulos: `Projeto`,
   `Stack`, `Arquivos`, `## Resumo`, `## Constatações`, `Arquivo:`,
   `Localizações:`, `Descrição:`, `Impacto:`, `Recomendação:`,
   `Mudança de contrato:`. Permanecem em inglês apenas a escala de severidade e
   os identificadores, conforme a seção "Idioma da saída" de
   `remediation-protocol.md`.
2. Escrever em linguagem clara e objetiva. Frases curtas, voz ativa, uma
   afirmação por frase. Não usar emoji nem sinal decorativo.
3. Cada constatação recebe um identificador próprio `F<NN>`, sequencial na
   ordem final do relatório, começando em `F01`. O identificador do catálogo
   vem logo depois, entre parênteses, no formato `(F07, C6)`. Os dois são
   necessários: o `F` é a chave única da constatação, o do catálogo é o padrão
   que ela instancia e se repete entre constatações.
4. `Arquivo:` traz caminho relativo à raiz do projeto e intervalo de linhas.
   Linha única é escrita como `arquivo.py:42`. Intervalo é escrito como
   `arquivo.py:42-58`. Ocorrências espalhadas no mesmo arquivo são escritas
   como `arquivo.py:12,28,45`.
5. `Localizações:` só é escrito quando a constatação alcança mais de um
   arquivo, e nesse caso lista todos, inclusive o de `Arquivo:`. É esse campo
   que impede a correção parcial: o registro de remediação abre uma linha por
   localização, e a constatação só fecha quando todas fecham.
6. `Impacto:` descreve consequência verificável, não julgamento.
7. `Recomendação:` nomeia a transformação do playbook a aplicar.
8. Constatação que altera o contrato recebe a marca `[altera-contrato]` ao
   final do título e o campo extra `Mudança de contrato:`. A marca não muda a
   posição da constatação: ela permanece ordenada pela própria severidade
   dentro de `## Constatações`. A listagem separada dessas constatações é o
   bloco impresso no passo 2.5, que fica fora do relatório.
9. O número em `Total:` é a soma das contagens de `## Resumo`.

## Estrutura obrigatória

```markdown
================================
RELATÓRIO DE AUDITORIA
================================
Projeto:  <nome do diretório raiz>
Stack:    <linguagem> + <framework> <versão>
Arquivos: <N> analisados | ~<N> linhas de código

## Resumo
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>

## Constatações

### [CRITICAL] <título curto> (<F>, <id do catálogo>)
Arquivo: <caminho>:<linhas>
Descrição: <o que foi encontrado, com o trecho ou o símbolo>
Impacto: <consequência verificável>
Recomendação: <ação e identificador da transformação>

### [CRITICAL] <título curto> (<F>, <id>) [altera-contrato]
Arquivo: <caminho>:<linhas>
Localizações: <caminho>:<linhas>, <caminho>:<linhas>
Descrição: <...>
Impacto: <...>
Recomendação: <...>
Mudança de contrato: <exatamente o que muda na resposta, no endpoint ou nos dados>

### [HIGH] <título curto> (<F>, <id>)
...

### [MEDIUM] <título curto> (<F>, <id>)
...

### [LOW] <título curto> (<F>, <id>)
...

================================
Total: <N> constatações
================================
```

Não existe linha de data. Data não é reproduzível entre execuções e não
acrescenta informação ao relatório.

## Ordenação

1. Severidade decrescente: CRITICAL, HIGH, MEDIUM, LOW.
2. Dentro da mesma severidade, ordem alfabética do caminho do arquivo.
3. Dentro do mesmo arquivo, ordem crescente da primeira linha.

A numeração `F` é atribuída depois da ordenação, seguindo a ordem final.

## Exemplo preenchido

Exemplo curto, com uma constatação de cada severidade e duas que alteram o
contrato. Serve como referência de formato, não como conteúdo a copiar.

```markdown
================================
RELATÓRIO DE AUDITORIA
================================
Projeto:  exemplo-api
Stack:    Python + Flask 3.1.1
Arquivos: 4 analisados | ~780 linhas de código

## Resumo
CRITICAL: 3 | HIGH: 1 | MEDIUM: 1 | LOW: 1

## Constatações

### [CRITICAL] Chave secreta embutida no código (F01, C2)
Arquivo: app.py:7
Localizações: app.py:7, controllers.py:289
Descrição: SECRET_KEY recebe um literal no código. O mesmo valor é devolvido
           pelo endpoint GET /health em controllers.py:289.
Impacto: A chave está no histórico de versionamento e não pode ser rotacionada
         sem alterar o código.
Recomendação: Remover o literal das duas localizações e ler de variável de
              ambiente. A chave não assina nada neste projeto, que não usa
              session nem flash, portanto pode ser gerada por boot quando a
              variável estiver ausente. Aplicar T2, categoria B.

### [CRITICAL] Chave secreta na resposta de /health (F02, C6) [altera-contrato]
Arquivo: controllers.py:285-289
Descrição: O corpo devolvido por GET /health inclui as chaves debug e
           secret_key com os valores de configuração da aplicação.
Impacto: Qualquer cliente com acesso ao endpoint obtém a chave de configuração
         sem autenticação.
Recomendação: Remover as chaves debug e secret_key do corpo. Aplicar T18.
Mudança de contrato: GET /health deixa de devolver as chaves debug e
                     secret_key. As demais chaves permanecem inalteradas.

### [CRITICAL] SQL Injection por concatenação (F03, C1)
Arquivo: models.py:28,48-49,110-111,140,291-293
Descrição: Consultas montadas por concatenação de string com valores vindos da
           requisição. Em models.py:110-111 os campos email e senha do corpo da
           requisição de login entram diretamente na cláusula WHERE.
Impacto: Um cliente pode alterar a estrutura da consulta e ler, alterar ou
         remover registros de qualquer tabela. A autenticação pode ser
         contornada com uma condição sempre verdadeira.
Recomendação: Substituir por consulta parametrizada com marcador posicional nas
              6 ocorrências. Aplicar T1.

### [HIGH] Estado global mutável na conexão de banco (F04, H3)
Arquivo: database.py:4-11
Descrição: A conexão é mantida em variável de módulo reatribuída por get_db,
           com check_same_thread desativado, e compartilhada por todas as
           requisições.
Impacto: Requisições concorrentes compartilham o mesmo cursor e a mesma
         transação. Um rollback disparado por uma requisição desfaz escrita de
         outra.
Recomendação: Substituir por fábrica de conexão com escopo de requisição.
              Aplicar T6.

### [MEDIUM] Validação de entrada incompleta (F05, M3) [altera-contrato]
Arquivo: controllers.py:64-96
Descrição: A rota de atualização de produto não valida tamanho de nome nem
           pertencimento de categoria à lista de categorias válidas, embora a
           rota de criação valide ambos.
Impacto: Um produto pode ser atualizado com nome de um caractere ou categoria
         inexistente, estado que a rota de criação recusa.
Recomendação: Aplicar as mesmas verificações da rota de criação. Aplicar T20.
Mudança de contrato: PUT /produtos/<id> passa a devolver 400 para nome fora da
                     faixa ou categoria inválida, entrada hoje aceita com 200.

### [LOW] Números mágicos nas faixas de desconto (F06, L1)
Arquivo: models.py:256-262
Descrição: Os limites 10000, 5000 e 1000 e as taxas 0.1, 0.05 e 0.02 aparecem
           como literais na cadeia condicional.
Impacto: O significado dos valores não é recuperável pela leitura e a alteração
         exige editar a função.
Recomendação: Extrair para constante nomeada no módulo de configuração,
              preservando os mesmos valores. Aplicar T13.

================================
Total: 6 constatações
================================
```

Observações sobre o exemplo:

- `F01` mostra o uso de `Localizações:`. A constatação alcança dois arquivos, e
  por isso vai gerar duas linhas no registro de remediação. Corrigir apenas
  `app.py:7` deixaria a constatação aberta.
- `F05` mostra uma constatação de severidade MEDIUM que altera o contrato. A
  marca não a promove nem a rebaixa: ela continua ordenada entre as MEDIUM, e
  aparece na lista do portão junto das CRITICAL que também alteram contrato.
- A ordem é CRITICAL `app.py`, CRITICAL `controllers.py`, CRITICAL `models.py`,
  HIGH, MEDIUM, LOW: severidade decrescente e, dentro da mesma severidade,
  ordem alfabética do caminho.

## Erros de preenchimento

| Erro | Correção |
|---|---|
| `Arquivo:` sem número de linha | Abrir o arquivo e registrar a linha exata |
| Intervalo de linhas estimado | Confirmar por leitura; não estimar |
| Constatação sem identificador `F` | Numerar na ordem final do relatório |
| Dois `F` repetidos | Renumerar; o `F` é chave única |
| Constatação em mais de um arquivo sem `Localizações:` | Acrescentar o campo com todas as localizações |
| `Impacto:` com julgamento em vez de consequência | Descrever o que acontece, não o quanto é ruim |
| `Recomendação:` sem identificador de transformação | Nomear a transformação do playbook |
| Constatação sem identificador de catálogo | Localizar a entrada correspondente |
| Total diferente da soma do resumo | Recontar |
| Constatação fora da ordem de severidade | Reordenar e renumerar os `F` |
| Constatação que altera contrato sem `Mudança de contrato:` | Acrescentar o campo |
| Rótulo em inglês | Traduzir; só severidade e identificadores ficam em inglês |
| Emoji ou sinal decorativo no relatório | Remover |
