// Orquestra GET /api/admin/financial-report. Movido de src/AppManager.js:80-129.

const { falha } = require('./httpError');

class ReportController {
    constructor({ reportModel }) {
        this.reportModel = reportModel;
    }

    financial = async (req, res, next) => {
        try {
            return res.ok(200, await this.reportModel.financial());
        } catch (erro) {
            // src/AppManager.js:84 devolvia 500 "Erro DB". O código e o texto
            // permanecem; o que muda é que o tratador central passa a registrar
            // a causa, em vez de o handler resolver o erro sozinho (M4).
            return next(falha(erro, 500, 'Erro DB'));
        }
    };
}

module.exports = ReportController;
