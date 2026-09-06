// T4 - Camada de rotas. Contém apenas a associação entre caminho, método e
// controller. Nenhum handler é definido aqui.
//
// O inventário da Fase 1 é reproduzido integralmente: três endpoints, mesmos
// caminhos e mesmos métodos.
//
// `adminGuard` chega por parâmetro, e não por importação, para que
// `middlewares` continue sendo importado apenas pelo ponto de entrada.

const { Router } = require('express');

module.exports = ({ checkoutController, reportController, userController, adminGuard }) => {
    const router = Router();

    router.post('/api/checkout', checkoutController.handle);
    router.get('/api/admin/financial-report', adminGuard, reportController.financial);
    router.delete('/api/users/:id', adminGuard, userController.remove);

    return router;
};
