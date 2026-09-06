// Orquestra POST /api/checkout. Movido de src/AppManager.js:28-78.
//
// T8: os cinco níveis de callback viraram sequência linear.
// T20: a verificação de entrada passou a cobrir tipo e formato (F16).
// T21: as variáveis locais têm nome completo; as chaves do corpo da requisição
//      continuam sendo `usr`, `eml`, `pwd`, `c_id` e `card`.
//
// O controller lê a entrada, valida o formato, chama o model e traduz o que ele
// devolve em corpo e código de status. Não recebe a conexão, não abre transação
// e não decide nada de domínio.

const logger = require('../config/logger');
const CheckoutModel = require('../models/checkoutModel');

const { ETAPAS, RESULTADOS } = CheckoutModel;

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARTAO = /^[0-9]{12,19}$/;

// Cada resultado e cada etapa que pode falhar tem um par fixo de código e
// texto. Os textos são os mesmos literais que src/AppManager.js produzia nos
// pontos correspondentes.
const POR_RESULTADO = {
    [RESULTADOS.CURSO_AUSENTE]: [404, 'Curso não encontrado'],
    [RESULTADOS.NAO_AUTENTICADO]: [401, 'Credenciais inválidas'],
    [RESULTADOS.RECUSADO]: [400, 'Pagamento recusado'],
};

// P2: até o portão estreito do passo 3.5 a falha de banco na consulta de curso
// respondia 404, como no código original. Agora os dois casos se separam: curso
// ausente continua 404, falha de banco passa a 500 "Erro DB".
const POR_ETAPA = {
    [ETAPAS.CONSULTA_CURSO]: [500, 'Erro DB'],
    [ETAPAS.CONSULTA_USUARIO]: [500, 'Erro DB'],
    [ETAPAS.CRIAR_USUARIO]: [500, 'Erro ao criar usuário'],
    [ETAPAS.MATRICULA]: [500, 'Erro Matrícula'],
    [ETAPAS.PAGAMENTO]: [500, 'Erro Pagamento'],
};

// F16: o código original verificava apenas presença (src/AppManager.js:35).
// Sem verificação de tipo, `card` numérico derrubava o processo em
// `cc.startsWith` e `c_id` textual persistia matrícula.
function formatoInvalido({ userName, email, password, courseId, cardNumber }) {
    if (typeof userName !== 'string') return 'usr deve ser um texto';
    if (!Number.isInteger(courseId)) return 'c_id deve ser um número inteiro';
    if (typeof cardNumber !== 'string' || !CARTAO.test(cardNumber)) {
        return 'card deve ser um texto de 12 a 19 dígitos';
    }
    if (typeof email !== 'string' || !EMAIL.test(email)) return 'eml deve ter formato de e-mail';
    if (typeof password !== 'string' || password.length === 0) return 'pwd é obrigatório';
    return null;
}

class CheckoutController {
    constructor({ checkoutModel }) {
        this.checkoutModel = checkoutModel;
    }

    handle = async (req, res, next) => {
        try {
            const {
                usr: userName, eml: email, pwd: password,
                c_id: courseId, card: cardNumber,
            } = req.body || {};

            // Verificação de presença preservada, com o mesmo texto e o mesmo
            // código de status de src/AppManager.js:35.
            if (!userName || !email || !courseId || !cardNumber) {
                return res.fail(400, 'Bad Request');
            }

            const invalido = formatoInvalido({ userName, email, password, courseId, cardNumber });
            if (invalido) return res.fail(400, invalido);

            // F02: nenhum dado sensível vai para o log. O número do cartão e a
            // chave do gateway saíram do conteúdo registrado.
            logger.debug('autorizando pagamento curso=%s email=%s', courseId, email);

            const saida = await this.checkoutModel.process({
                userName, email, password, courseId, cardNumber,
            });

            const recusa = POR_RESULTADO[saida.resultado];
            if (recusa) return res.fail(recusa[0], recusa[1]);

            logger.info(
                'checkout concluído curso=%s usuário=%s matrícula=%s status=%s',
                courseId, saida.userId, saida.enrollmentId, saida.status
            );
            return res.ok(200, { msg: 'Sucesso', enrollment_id: saida.enrollmentId });
        } catch (erro) {
            const falha = POR_ETAPA[erro && erro.etapa];
            if (!falha) return next(erro);
            logger.error('falha na etapa %s do checkout', erro.etapa, erro);
            return res.fail(falha[0], falha[1]);
        }
    };
}

module.exports = CheckoutController;
