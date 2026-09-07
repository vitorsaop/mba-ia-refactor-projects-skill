"""Configuração de registro de log, T23.

Substitui as chamadas a print espalhadas pelos handlers por registro com
nível e destino configurável.
"""
import logging

from src.config import settings


def configure(level=None):
    logging.basicConfig(
        level=level or settings.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
