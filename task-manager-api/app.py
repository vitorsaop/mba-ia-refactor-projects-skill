"""Ponto de entrada preservado.

O caminho, o nome do arquivo e os símbolos `app` e `db` continuam os mesmos,
portanto `python app.py` funciona sem alteração e `seed.py` continua
importando daqui.
"""
from src.app import create_app
from src.config import settings
from src.config.database import db

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
