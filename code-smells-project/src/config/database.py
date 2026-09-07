"""Fábrica de conexão.

A criação de esquema e a carga inicial saíram daqui para `src/models/`, F09:
a camada de configuração não contém consulta.
"""
import sqlite3
from contextlib import contextmanager

from src.config.settings import DB_PATH


@contextmanager
def get_connection(path=None):
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
