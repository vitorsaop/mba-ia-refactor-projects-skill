// Caso de uso do checkout: a sequência inteira que POST /api/checkout executa,
// dentro de uma transação. Movida de src/AppManager.js:28-78.
//
// Vive na camada de model, e não no controller, porque a fronteira transacional
// e a ordem das operações são regra de domínio. O controller não recebe a
// conexão e não sabe que existe transação.
//
// As LEITURAS que decidem o resultado ficam dentro da transação, junto com as
// escritas. Fora dela, dois checkouts concorrentes com o mesmo e-mail novo leem
// "não existe" e ambos inserem, porque `users.email` não tem restrição de
// unicidade, e o preço lido pode não ser o vigente no instante da escrita.
//
// Este módulo não conhece HTTP. Ele nomeia o RESULTADO e, quando uma operação
// falha, a ETAPA; é o controller que traduz um e outro em código de status.

const { verifyPassword } = require('./password');

const ETAPAS = {
    CONSULTA_CURSO: 'consultaCurso',
    CONSULTA_USUARIO: 'consultaUsuario',
    CRIAR_USUARIO: 'criarUsuario',
    MATRICULA: 'matricula',
    PAGAMENTO: 'pagamento',
};

const RESULTADOS = {
    CURSO_AUSENTE: 'cursoAusente',
    NAO_AUTENTICADO: 'naoAutenticado',
    RECUSADO: 'recusado',
    CONCLUIDO: 'concluido',
};

function porEtapa(etapa) {
    return (causa) => {
        causa.etapa = etapa;
        throw causa;
    };
}

class CheckoutModel {
    constructor({ db, courseModel, userModel, enrollmentModel, paymentModel, auditModel }) {
        Object.assign(this, {
            db, courseModel, userModel, enrollmentModel, paymentModel, auditModel,
        });
    }

    process({ userName, email, password, courseId, cardNumber }) {
        return this.db.transaction(async () => {
            const course = await this.courseModel
                .findActiveById(courseId)
                .catch(porEtapa(ETAPAS.CONSULTA_CURSO));

            if (!course) return { resultado: RESULTADOS.CURSO_AUSENTE };

            const existente = await this.userModel
                .findByEmail(email)
                .catch(porEtapa(ETAPAS.CONSULTA_USUARIO));

            // P3: até o portão estreito do passo 3.5, o e-mail sozinho bastava
            // para matricular e cobrar em nome de quem já estava cadastrado.
            if (existente && !await verifyPassword(password, existente.pass)) {
                return { resultado: RESULTADOS.NAO_AUTENTICADO };
            }

            // A ordem original é preservada: o usuário é criado ANTES da
            // autorização do pagamento, portanto um pagamento recusado continua
            // deixando o usuário cadastrado. Por isso o caminho de recusa sai da
            // transação por COMMIT, e não por ROLLBACK.
            const userId = existente
                ? existente.id
                : await this.userModel
                    .create(userName, email, password)
                    .catch(porEtapa(ETAPAS.CRIAR_USUARIO));

            const status = this.paymentModel.authorize(cardNumber);

            if (this.paymentModel.isDenied(status)) {
                return { resultado: RESULTADOS.RECUSADO, userId };
            }

            const enrollmentId = await this.enrollmentModel
                .create(userId, courseId)
                .catch(porEtapa(ETAPAS.MATRICULA));

            await this.paymentModel
                .record(enrollmentId, course.price, status)
                .catch(porEtapa(ETAPAS.PAGAMENTO));

            await this.auditModel.record(`Checkout curso ${courseId} por ${userId}`);

            return { resultado: RESULTADOS.CONCLUIDO, status, userId, enrollmentId };
        });
    }
}

module.exports = CheckoutModel;
module.exports.ETAPAS = ETAPAS;
module.exports.RESULTADOS = RESULTADOS;
