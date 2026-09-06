// Criação de esquema e carga inicial, movidas de src/AppManager.js:10-23.
//
// As cinco tabelas e as quatro linhas de carga são as mesmas, com os mesmos
// valores. Três diferenças: a senha do usuário semeado passa pela mesma
// derivação usada no cadastro (F05); as escritas acontecem em uma transação,
// para que um boot interrompido no meio não deixe esquema pela metade; e a
// rotina é idempotente.
//
// A idempotência é necessária porque `DB_FILE` tornou o banco configurável. Com
// `:memory:`, que é o padrão e o valor que o código original tinha fixo, o
// banco nasce vazio a cada boot e nada muda. Apontando para um arquivo, um
// `CREATE TABLE` incondicional derrubaria o segundo boot com "table users
// already exists", e o ponto de entrada encerra o processo quando esta rotina
// falha.

const settings = require('../config/settings');
const { hashPassword } = require('./password');

const ESQUEMA = `
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
    CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
    CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
    CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
    CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

const USUARIO_INICIAL = { nome: 'Leonan', email: 'leonan@fullcycle.com.br' };

async function criarEsquema(db) {
    await db.exec(ESQUEMA);
}

async function carregarDados(db) {
    await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [USUARIO_INICIAL.nome, USUARIO_INICIAL.email, await hashPassword(settings.seedUserPassword)]
    );
    await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
        ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]
    );
    await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
    await db.run(
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [1, 997.00, settings.payment.statusApproved]
    );
}

async function create(db) {
    await db.transaction(async () => {
        await criarEsquema(db);
        // A carga só roda em banco vazio. Sem isso, cada boot sobre um arquivo
        // existente duplicaria o usuário semeado, os dois cursos, a matrícula e
        // o pagamento.
        const { total } = await db.get('SELECT COUNT(*) AS total FROM users', []);
        if (total === 0) await carregarDados(db);
    });
}

module.exports = { create };
