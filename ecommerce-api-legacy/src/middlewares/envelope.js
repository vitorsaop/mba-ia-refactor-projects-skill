// T22 - Padronização de envelope de resposta. Constatação F22, autorizada no
// portão da Fase 2, item [5].
//
// Registrado antes das rotas, acrescenta `res.ok` e `res.fail`. Nenhum
// controller monta o envelope por conta própria, e por isso os três endpoints
// devolvem a mesma forma.
//
//   sucesso: { "sucesso": true,  "dados": <carga original> }
//   falha:   { "sucesso": false, "erro":  <texto original> }
//
// A carga e o texto dentro do envelope são exatamente os da linha de base.

module.exports = (req, res, next) => {
    res.ok = (status, dados) => res.status(status).json({ sucesso: true, dados });
    res.fail = (status, erro) => res.status(status).json({ sucesso: false, erro });
    return next();
};
