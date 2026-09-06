// T11 - Tratamento de erro por handler para tratador centralizado.
//
// Último middleware registrado. Os quatro parâmetros são obrigatórios para que
// o Express o reconheça como tratador de erro, mesmo com `next` não sendo
// chamado: a resposta termina aqui.
//
// `status` e `publicMessage` são anexados pelos controllers, por
// src/controllers/httpError.js, para preservar os textos que o código original
// produzia em cada ponto de falha. Este arquivo não importa aquele módulo, então
// nenhuma seta de importação aponta de `middlewares` para `controllers`.

const logger = require('../config/logger');

const STATUS_PADRAO = 500;
const TEXTO_PADRAO = 'Erro interno';

module.exports = (erro, req, res, next) => {
    logger.error('erro não tratado', erro);

    if (res.headersSent) return next(erro);

    // O status vem do erro quando ele traz um: os controllers anexam o seu por
    // httpError.js, e o parser de corpo do Express anexa 400 no JSON malformado.
    const status = Number.isInteger(erro && erro.status) ? erro.status : STATUS_PADRAO;
    const texto = (erro && erro.publicMessage) || TEXTO_PADRAO;

    // `res.fail` existe sempre: `envelope` é o primeiro middleware registrado
    // em src/app.js, antes do parser de corpo, das rotas e deste tratador. Uma
    // reserva aqui seria ramo inalcançável e uma segunda definição do formato
    // do envelope, que divergiria da primeira sem ninguém perceber.
    return res.fail(status, texto);
};
