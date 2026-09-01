import logging
import os


def configurar_logging():
    """Configura logging básico sin incluir secretos ni datos sensibles."""
    nivel = getattr(logging, os.getenv("POS_LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=nivel, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return logging.getLogger("factra")


logger = configurar_logging()
