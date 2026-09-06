// T6 - Conexão global e instanciação concreta para fábrica injetada.
//
// Toda instanciação concreta fica aqui, e este arquivo é chamado apenas pelo
// ponto de entrada. Nenhum model conhece o driver: cada um recebe a conexão
// pelo construtor. Cada controller recebe apenas o que usa.

const sqlite3 = require('sqlite3');
const settings = require('./config/settings');
const { envolver } = require('./config/db');
const schema = require('./models/schema');
const CourseModel = require('./models/courseModel');
const UserModel = require('./models/userModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditModel = require('./models/auditModel');
const ReportModel = require('./models/reportModel');
const CheckoutModel = require('./models/checkoutModel');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');

module.exports = () => {
    // F14: o modo verboso do driver deixa de estar ligado incondicionalmente.
    const driverModule = settings.sqliteVerbose ? sqlite3.verbose() : sqlite3;

    // Banco em memória: a instância é única e compartilhada. Abrir uma conexão
    // por operação criaria um banco vazio a cada chamada.
    const driver = new driverModule.Database(settings.dbFile);

    // Modo serializado: as instruções desta conexão passam a ser executadas em
    // ordem. Junto com a fila de transações de config/db.js, é o que remove a
    // não-determinação de ordem registrada em .refactor-arch/runtime.md.
    driver.serialize();

    const db = envolver(driver);

    const courseModel = new CourseModel(db);
    const userModel = new UserModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditModel = new AuditModel(db);
    const reportModel = new ReportModel(db);
    const checkoutModel = new CheckoutModel({
        db, courseModel, userModel, enrollmentModel, paymentModel, auditModel,
    });

    return {
        initDb: () => schema.create(db),
        checkoutController: new CheckoutController({ checkoutModel }),
        reportController: new ReportController({ reportModel }),
        userController: new UserController({ userModel }),
    };
};
