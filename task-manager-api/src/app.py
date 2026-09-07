"""Composition root: compõe as camadas e inicializa a aplicação."""
from flask import Flask
from flask_cors import CORS

from src.config import logging_config, settings
from src.config.database import db
from src.middlewares import error_handler
from src.views.routes import BLUEPRINTS


def create_app():
    logging_config.configure()

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG

    # T19 com o padrão restritivo autorizado no item [4] do portão: lista
    # vazia significa nenhuma origem cruzada permitida.
    if settings.CORS_ORIGINS:
        CORS(app, origins=settings.CORS_ORIGINS)

    db.init_app(app)

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    error_handler.register(app)

    with app.app_context():
        import src.models  # noqa: F401  registra os modelos antes de criar o esquema
        db.create_all()

    return app
