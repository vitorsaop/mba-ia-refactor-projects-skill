// T17 - Senha em texto puro ou digest fraco para digest com sal.
//
// Substitui `badCrypto` de src/utils.js:17-23, que concatenava 10.000 vezes o
// mesmo par de caracteres do base64 da senha e devolvia os 10 primeiros: sem
// sal, reversível por tabela pré-computada sobre o início da senha, e com custo
// que não acrescentava resistência.
//
// `crypto.pbkdf2` e `crypto.timingSafeEqual` são da biblioteca padrão do Node,
// portanto a transformação não introduz dependência nova.

const crypto = require('crypto');
const settings = require('../config/settings');

const { algorithm, iterations, saltBytes, keyBytes } = settings.password;
const PREFIXO = `pbkdf2_${algorithm}`;
const SEPARADOR = '$';

function derivar(senha, sal, voltas, tamanho) {
    return new Promise((resolve, reject) => {
        crypto.pbkdf2(senha, sal, voltas, tamanho, algorithm, (erro, derivado) => (
            erro ? reject(erro) : resolve(derivado)
        ));
    });
}

async function hashPassword(senha) {
    const sal = crypto.randomBytes(saltBytes);
    const derivado = await derivar(senha, sal, iterations, keyBytes);
    return [PREFIXO, iterations, sal.toString('hex'), derivado.toString('hex')].join(SEPARADOR);
}

// P3: verificação da senha de usuário já cadastrado. Autorizada no portão
// estreito do passo 3.5. Comparação em tempo constante.
//
// Devolve false, e nunca lança, para qualquer valor armazenado que não esteja no
// formato produzido por hashPassword. Um registro gravado pelo esquema antigo
// simplesmente não valida.
async function verifyPassword(senha, armazenado) {
    if (typeof senha !== 'string' || typeof armazenado !== 'string') return false;

    const partes = armazenado.split(SEPARADOR);
    if (partes.length !== 4) return false;

    const [prefixo, voltas, salHex, digestHex] = partes;
    if (prefixo !== PREFIXO) return false;

    const numeroDeVoltas = Number(voltas);
    if (!Number.isInteger(numeroDeVoltas) || numeroDeVoltas <= 0) return false;
    if (!/^[0-9a-f]+$/.test(salHex) || !/^[0-9a-f]+$/.test(digestHex)) return false;

    const esperado = Buffer.from(digestHex, 'hex');
    const derivado = await derivar(senha, Buffer.from(salHex, 'hex'), numeroDeVoltas, esperado.length);

    return derivado.length === esperado.length && crypto.timingSafeEqual(derivado, esperado);
}

module.exports = { hashPassword, verifyPassword };
