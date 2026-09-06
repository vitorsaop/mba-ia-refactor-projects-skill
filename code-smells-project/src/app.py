from flask import Flask
from flask_cors import CORS

from src.config import settings, logging_config
from src.config.database import init_db
from src.views.routes import ALL_BLUEPRINTS
from src.middlewares import error_handler


def create_app():
    logging_config.configure()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)

    init_db()

    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)

    error_handler.register(app)
    return app
