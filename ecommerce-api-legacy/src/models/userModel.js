// Acesso a dados de usuário. Movido de src/AppManager.js:40,69,133.

const { hashPassword } = require('./password');

class UserModel {
    constructor(db) {
        this.db = db;
    }

    // Devolve também o valor armazenado da senha, porque P3 passou a exigir a
    // verificação. Quem consome é checkoutModel, que compara e descarta: o
    // digest não sai da camada de model.
    findByEmail(email) {
        return this.db.get('SELECT id, pass FROM users WHERE email = ?', [email]);
    }

    async create(nome, email, senha) {
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [nome, email, await hashPassword(senha)]
        );
        return lastID;
    }

    // F12: a remoção passa a alcançar as linhas dependentes. A ordem vai da
    // ponta para a raiz, para que nenhuma referência sobreviva ao alvo, e a
    // transação é aberta aqui: a atomicidade é propriedade desta operação, não
    // uma obrigação que o chamador precise lembrar de cumprir.
    removeWithDependents(userId) {
        return this.db.transaction(async () => {
            await this.db.run(
                'DELETE FROM payments WHERE enrollment_id IN '
                + '(SELECT id FROM enrollments WHERE user_id = ?)',
                [userId]
            );
            await this.db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
            await this.db.run('DELETE FROM users WHERE id = ?', [userId]);
        });
    }
}

module.exports = UserModel;
