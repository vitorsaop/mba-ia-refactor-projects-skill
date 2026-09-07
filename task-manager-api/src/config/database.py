"""Instância única de mapeamento objeto-relacional.

Fica na camada de configuração, e não na raiz do projeto, para que a seta de
importação dos modelos aponte para dentro.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
