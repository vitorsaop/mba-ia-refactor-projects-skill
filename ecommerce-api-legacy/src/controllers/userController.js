// Orquestra DELETE /api/users/:id. Movido de src/AppManager.js:131-137.
//
// O controller não recebe a conexão: a transação da remoção em cascata é do
// model de usuário.

const { falha } = require('./httpError');

// P1: o texto original, "Usuário deletado, mas as matrículas e pagamentos
// ficaram sujos no banco.", descrevia o defeito que F12 corrigiu e por isso
// passou a ser falso. A troca foi autorizada no portão estreito do passo 3.5;
// até lá o literal antigo foi preservado, porque alterar texto de resposta é
// mudança de contrato.
const MENSAGEM_REMOCAO = 'Usuário removido, junto com as matrículas e os pagamentos associados.';

// F16: o identificador seguia direto para a consulta. Um único mecanismo
// decide, para que não haja duas definições divergentes de "inteiro".
function identificadorValido(bruto) {
    if (!/^[0-9]+$/.test(bruto)) return null;
    const numero = Number(bruto);
    return Number.isSafeInteger(numero) ? numero : null;
}

class UserController {
    constructor({ userModel }) {
        this.userModel = userModel;
    }

    remove = async (req, res, next) => {
        const userId = identificadorValido(req.params.id);
        if (userId === null) return res.fail(400, 'id deve ser um número inteiro');

        try {
            await this.userModel.removeWithDependents(userId);
            return res.ok(200, MENSAGEM_REMOCAO);
        } catch (erro) {
            // src/AppManager.js:133 respondia sucesso mesmo quando a remoção
            // falhava. O erro passa a chegar ao tratador central (F11), que
            // devolve o mesmo 500 do código original.
            return next(falha(erro, 500, 'Erro interno'));
        }
    };
}

module.exports = UserController;
