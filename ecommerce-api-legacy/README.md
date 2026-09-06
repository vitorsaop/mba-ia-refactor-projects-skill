# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Variáveis de ambiente

Todas têm valor padrão, exceto `ADMIN_TOKEN`. Copiar `.env.example` e exportar
no shell as que precisar alterar.

| Variável | Padrão | Para que serve |
|---|---|---|
| `PORT` | `3000` | porta em que a aplicação escuta |
| `DB_FILE` | `:memory:` | caminho do banco SQLite |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |
| `SQLITE_VERBOSE` | `false` | modo verboso do driver |
| `SEED_USER_PASSWORD` | `123` | senha do usuário da carga inicial |
| `ADMIN_TOKEN` | sem padrão | credencial dos endpoints administrativos |

`GET /api/admin/financial-report` e `DELETE /api/users/:id` exigem o cabeçalho
`X-Admin-Token` com o valor de `ADMIN_TOKEN`. Enquanto a variável estiver
indefinida, os dois recusam toda requisição com 401.

`POST /api/checkout` exige `usr`, `eml`, `pwd`, `c_id` inteiro e `card` com 12 a
19 dígitos. Quando o e-mail já está cadastrado, a senha é conferida contra o
digest gravado: não conferindo, a resposta é 401. O usuário da carga inicial é
`leonan@fullcycle.com.br`, com a senha de `SEED_USER_PASSWORD`.

## Estrutura

```
src/
├── app.js          ponto de entrada e composição
├── container.js    instanciação concreta
├── config/         ambiente, conexão e log
├── models/         dados e regra de negócio
├── controllers/    orquestração da requisição
├── routes/         caminho, método e controller
└── middlewares/    envelope, credencial e erro
```
