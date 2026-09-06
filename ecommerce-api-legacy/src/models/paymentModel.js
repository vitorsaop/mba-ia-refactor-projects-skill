// Regra de aprovação e persistência de pagamento.
// Movidas de src/AppManager.js:46 e :54.

const settings = require('../config/settings');

class PaymentModel {
    constructor(db) {
        this.db = db;
    }

    // Regra de negócio preservada palavra por palavra: cartão iniciado em "4" é
    // aprovado, qualquer outro é recusado. O prefixo e os dois rótulos vivem em
    // config/settings.js com exatamente os mesmos valores.
    authorize(cardNumber) {
        return cardNumber.startsWith(settings.payment.approvedCardPrefix)
            ? settings.payment.statusApproved
            : settings.payment.statusDenied;
    }

    isDenied(status) {
        return status === settings.payment.statusDenied;
    }

    record(enrollmentId, amount, status) {
        return this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
    }
}

module.exports = PaymentModel;
