// Anexa a um erro o código de status e o texto que a resposta deve carregar.
//
// Existe para que os textos que o código original produzia em cada ponto de
// falha - "Erro Matrícula", "Erro Pagamento", "Erro ao criar usuário" - sejam
// preservados depois de T11 centralizar o tratamento. O tratador central lê as
// duas propriedades sem importar este módulo, então nenhuma seta de importação
// aponta de `middlewares` para `controllers`.

function falha(erro, status, textoPublico) {
    erro.status = status;
    erro.publicMessage = textoPublico;
    return erro;
}

module.exports = { falha };
