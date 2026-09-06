import logging

from src.app import create_app
from src.config.settings import PORT, DEBUG

app = create_app()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("SERVIDOR INICIADO")
    logger.info("Rodando em http://localhost:%s", PORT)
    logger.info("=" * 50)
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
