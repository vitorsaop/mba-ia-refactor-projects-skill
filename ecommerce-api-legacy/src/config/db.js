// T8 - Adaptador de promessa sobre o driver de callback do sqlite3.
// T9 - Escopo de transação.
//
// É a única peça do projeto que conhece a forma do driver. Os models recebem
// este objeto e nunca o instanciam.

const { AsyncLocalStorage } = require('async_hooks');

const envolver = (driver) => {
    // Acesso direto ao driver. Só o controle de exclusividade abaixo o usa.
    const bruto = {
        get: (sql, parametros) => new Promise((resolve, reject) => {
            driver.get(sql, parametros, (erro, linha) => (erro ? reject(erro) : resolve(linha)));
        }),
        all: (sql, parametros) => new Promise((resolve, reject) => {
            driver.all(sql, parametros, (erro, linhas) => (erro ? reject(erro) : resolve(linhas)));
        }),
        // `function` em vez de arrow function porque `this.lastID` é fornecido
        // pelo driver no contexto do callback.
        run: (sql, parametros) => new Promise((resolve, reject) => {
            driver.run(sql, parametros, function retorno(erro) {
                return erro
                    ? reject(erro)
                    : resolve({ lastID: this.lastID, changes: this.changes });
            });
        }),
        exec: (sql) => new Promise((resolve, reject) => {
            driver.exec(sql, (erro) => (erro ? reject(erro) : resolve()));
        }),
    };

    // Exclusividade sobre a conexão.
    //
    // A conexão é única. No SQLite, QUALQUER instrução emitida em uma conexão
    // com transação aberta pertence a essa transação: uma leitura de outra
    // requisição enxerga linhas ainda não commitadas, e some com elas no
    // rollback. Serializar só as transações não basta; foi medido: com uma
    // transação aberta, `SELECT` de fora devolveu a linha não commitada, e
    // depois do ROLLBACK ela desapareceu.
    //
    // Por isso toda operação passa pela fila, não apenas `transaction`.
    //
    // `AsyncLocalStorage`, da biblioteca padrão do Node, distingue a chamada
    // vinda de DENTRO do corpo de uma transação, que já detém a exclusividade e
    // travaria a si mesma se enfileirasse, da chamada vinda de outra
    // requisição, que precisa esperar.
    const escopo = new AsyncLocalStorage();
    let fila = Promise.resolve();

    const exclusivo = (corpo) => {
        if (escopo.getStore()) return corpo();
        const atual = fila.then(() => escopo.run(true, corpo));
        // A fila avança mesmo quando a operação falha. Sem os dois ramos, uma
        // falha deixaria todas as operações seguintes presas.
        fila = atual.then(() => undefined, () => undefined);
        return atual;
    };

    const get = (sql, parametros = []) => exclusivo(() => bruto.get(sql, parametros));
    const all = (sql, parametros = []) => exclusivo(() => bruto.all(sql, parametros));
    const run = (sql, parametros = []) => exclusivo(() => bruto.run(sql, parametros));
    const exec = (sql) => exclusivo(() => bruto.exec(sql));

    // Uma sequência de escritas relacionadas termina em COMMIT ou em ROLLBACK,
    // nunca em estado parcial, e nenhuma leitura de fora atravessa a sequência.
    const transaction = (corpo) => exclusivo(async () => {
        // Chamada de dentro de outra transação junta-se à que já está aberta,
        // em vez de emitir um segundo BEGIN, que o SQLite recusa.
        if (escopo.getStore() === 'transacao') return corpo();

        return escopo.run('transacao', async () => {
            await bruto.exec('BEGIN');
            try {
                const resultado = await corpo();
                await bruto.exec('COMMIT');
                return resultado;
            } catch (erro) {
                try {
                    await bruto.exec('ROLLBACK');
                } catch (erroDoRollback) {
                    // O erro original é a causa e continua sendo o que sobe. O
                    // do rollback viaja junto, para não desaparecer.
                    erro.rollbackError = erroDoRollback;
                }
                throw erro;
            }
        });
    });

    return { get, all, run, exec, transaction };
};

module.exports = { envolver };
