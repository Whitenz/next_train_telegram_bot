import logging

from app.bot import start_bot

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    try:
        start_bot()
    except Exception:
        logger.exception('Ошибка при старте бота')
