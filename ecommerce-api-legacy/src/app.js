// T15 - Ponto de entrada e composition root.
//
// O caminho e o nome deste arquivo são preservados: `npm start` continua sendo
// `node src/app.js`, exatamente como package.json e README.md documentam.
//
// Aqui só existe composição. Nenhuma rota, nenhuma consulta, nenhuma regra.

const express = require('express');
const settings = require('./config/settings');
const logger = require('./config/logger');
const construirContainer = require('./container');
const construirRotas = require('./routes');
const envelope = require('./middlewares/envelope');
const adminGuard = require('./middlewares/adminGuard');
const errorHandler = require('./middlewares/errorHandler');

const app = express();

// O envelope vem ANTES do parser de corpo. Se viesse depois, um corpo JSON
// malformado faria o parser lançar antes de `res.ok` e `res.fail` existirem, e
// o tratador central falharia ao montar a resposta: o 400 do parser virava 500.
app.use(envelope);
app.use(express.json());

const { initDb, checkoutController, reportController, userController } = construirContainer();

app.use(construirRotas({ checkoutController, reportController, userController, adminGuard }));
app.use(errorHandler);

initDb()
    .then(() => {
        app.listen(settings.port, () => {
            logger.info('Frankenstein LMS rodando na porta %s...', settings.port);
        });
    })
    .catch((erro) => {
        logger.error('falha ao criar o esquema e a carga inicial', erro);
        process.exit(1);
    });
