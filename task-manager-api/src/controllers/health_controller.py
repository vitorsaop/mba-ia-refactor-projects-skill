"""Handlers das duas rotas que estavam no ponto de entrada, F23."""
import datetime

from src.controllers import envelope


def index():
    return envelope.ok({"message": "Task Manager API", "version": "1.0"})


def health():
    return envelope.ok({"status": "ok", "timestamp": str(datetime.datetime.now())})
