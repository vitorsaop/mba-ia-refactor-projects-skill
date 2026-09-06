// T2 - Segredo e sinalizador embutido para módulo de configuração.
//
// Categoria A, valor não secreto: o literal que o projeto já tinha vira o valor
// padrão, para que `npm start` continue funcionando sem nenhuma variável
// definida. Origem dos literais: `port: 3000` de src/utils.js:6 e `':memory:'`
// de src/AppManager.js:7.
//
// Categoria C, segredo com verificação externa: sem literal e sem valor padrão.
// Ausente a variável, quem consome recusa a operação.

const comoBooleano = (valor, padrao) => {
    if (valor === undefined || valor === '') return padrao;
    return ['1', 'true', 'yes', 'on'].includes(String(valor).toLowerCase());
};

module.exports = {
    port: Number(process.env.PORT || 3000),
    dbFile: process.env.DB_FILE || ':memory:',
    logLevel: process.env.LOG_LEVEL || 'info',

    // F14: o modo verboso do driver deixa de estar ligado incondicionalmente.
    // Padrão desligado, como T2 prescreve para sinalizador de depuração.
    sqliteVerbose: comoBooleano(process.env.SQLITE_VERBOSE, false),

    // Senha do usuário da carga inicial. Continua sendo '123' por padrão, que é
    // o valor que src/AppManager.js:18 gravava, para não alterar a credencial
    // desse usuário. Passou a ser substituível sem editar código.
    seedUserPassword: process.env.SEED_USER_PASSWORD || '123',

    // Categoria C. Exposta como função para que a ausência falhe no uso e não
    // no carregamento do módulo: a aplicação sobe e os endpoints que não
    // dependem dela continuam respondendo.
    adminToken: () => process.env.ADMIN_TOKEN || '',

    // T13: parâmetros de derivação de senha, biblioteca padrão do Node.
    password: {
        algorithm: 'sha256',
        iterations: 240000,
        saltBytes: 16,
        keyBytes: 32,
    },

    // T13: literais de decisão de pagamento preservados de src/AppManager.js:46.
    // O valor de cada um é exatamente o mesmo; o que muda é ter nome.
    payment: {
        approvedCardPrefix: '4',
        statusApproved: 'PAID',
        statusDenied: 'DENIED',
    },
};
