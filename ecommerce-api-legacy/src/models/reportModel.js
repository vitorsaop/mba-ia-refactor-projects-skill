// T7 - Consulta em laço para consulta única.
//
// O handler original (src/AppManager.js:83-127) executava 1 + C + 2xM consultas:
// uma de cursos, uma de matrículas por curso, e uma de usuário mais uma de
// pagamento por matrícula. Aqui é uma só.
//
// Os três LEFT JOIN preservam os casos que o código original tratava com valor
// de reserva: curso sem matrícula devolve lista de alunos vazia, matrícula com
// usuário removido devolve 'Unknown', matrícula sem pagamento devolve 0.
//
// O ORDER BY torna determinística uma ordem que antes vinha da conclusão dos
// callbacks no pool de threads do driver e variava entre duas execuções do
// mesmo código. Ver .refactor-arch/runtime.md.

const settings = require('../config/settings');

const ALUNO_DESCONHECIDO = 'Unknown';
const SEM_PAGAMENTO = 0;

const SQL = `
    SELECT c.id     AS course_id,
           c.title  AS course_title,
           e.id     AS enrollment_id,
           u.id     AS student_id,
           u.name   AS student_name,
           p.id     AS payment_id,
           p.amount AS payment_amount,
           p.status AS payment_status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users       u ON u.id = e.user_id
      LEFT JOIN payments    p ON p.enrollment_id = e.id
     ORDER BY c.id, e.id, p.id
`;

class ReportModel {
    constructor(db) {
        this.db = db;
    }

    async financial() {
        const linhas = await this.db.all(SQL, []);
        const porCurso = new Map();
        // `db.get` devolvia a primeira linha de payments por matrícula. O
        // ORDER BY p.id garante que a primeira linha vista aqui é a mesma.
        const matriculasVistas = new Set();

        for (const linha of linhas) {
            if (!porCurso.has(linha.course_id)) {
                porCurso.set(linha.course_id, {
                    course: linha.course_title,
                    revenue: 0,
                    students: [],
                });
            }

            if (linha.enrollment_id === null) continue;
            if (matriculasVistas.has(linha.enrollment_id)) continue;
            matriculasVistas.add(linha.enrollment_id);

            const curso = porCurso.get(linha.course_id);

            if (linha.payment_status === settings.payment.statusApproved) {
                curso.revenue += linha.payment_amount;
            }

            curso.students.push({
                student: linha.student_id === null ? ALUNO_DESCONHECIDO : linha.student_name,
                paid: linha.payment_id === null ? SEM_PAGAMENTO : linha.payment_amount,
            });
        }

        return [...porCurso.values()];
    }
}

module.exports = ReportModel;
