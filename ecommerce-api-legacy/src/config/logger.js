// T23 - Saída em terminal para registro com nível.
//
// Encapsulamento próprio, sem acrescentar dependência. Substitui os três
// `console.log` do código original (src/app.js:13, src/utils.js:13 e
// src/AppManager.js:45).
//
// Nenhum dado sensível vai para o log em nenhum nível: número de cartão, senha
// e chave de gateway não entram no conteúdo registrado.

const settings = require('./settings');

const NIVEIS = { error: 0, warn: 1, info: 2, debug: 3 };
const DESTINO = { error: 'error', warn: 'warn', info: 'info', debug: 'log' };

const atual = NIVEIS[settings.logLevel] !== undefined ? NIVEIS[settings.logLevel] : NIVEIS.info;

// A etiqueta de nível entra no primeiro argumento, e não como argumento
// separado, para que o console continue interpretando `%s` como marcador de
// formato. Passada à parte, a etiqueta viraria o formato e o resto sairia cru.
const emitir = (nivel, argumentos) => {
    if (NIVEIS[nivel] > atual) return;
    const etiqueta = `[${nivel.toUpperCase()}]`;
    const [primeiro, ...resto] = argumentos;
    if (typeof primeiro === 'string') {
        console[DESTINO[nivel]](`${etiqueta} ${primeiro}`, ...resto);
    } else {
        console[DESTINO[nivel]](etiqueta, ...argumentos);
    }
};

// Acrescentar um nível passa a ser acrescentar uma entrada em NIVEIS e outra em
// DESTINO. A interface é derivada, não escrita à mão.
module.exports = Object.fromEntries(
    Object.keys(NIVEIS).map((nivel) => [nivel, (...argumentos) => emitir(nivel, argumentos)])
);
