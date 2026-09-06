// T16, opção B, proteção. Constatação F03, autorizada no portão da Fase 2,
// item [1].
//
// A credencial é categoria C de T2: sem literal no código e sem valor padrão.
// Com a variável indefinida a resposta é a recusa, e o aviso nomeia o que
// falta. Falhar no carregamento derrubaria também os endpoints que não dependem
// dela.

const crypto = require('crypto');
const settings = require('../config/settings');
const logger = require('../config/logger');

const CABECALHO = 'x-admin-token';
const RECUSA = 'Não autorizado';

module.exports = (req, res, next) => {
    const esperado = settings.adminToken();

    if (!esperado) {
        logger.warn(
            'ADMIN_TOKEN não definida: toda requisição administrativa será recusada. '
            + 'Copiar .env.example para .env e preencher.'
        );
        return res.fail(401, RECUSA);
    }

    const enviado = Buffer.from(req.get(CABECALHO) || '');
    const referencia = Buffer.from(esperado);

    // Comparação em tempo constante. O teste de tamanho vem antes porque
    // timingSafeEqual exige buffers do mesmo comprimento.
    if (enviado.length !== referencia.length || !crypto.timingSafeEqual(enviado, referencia)) {
        return res.fail(401, RECUSA);
    }

    return next();
};
