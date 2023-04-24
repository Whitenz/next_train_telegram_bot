import logging
import os.path
import sys

from app.bot import start_bot
from app.config import BOT_TOKEN, DB_FILENAME

logger = logging.getLogger(__name__)


def check_environment_variables() -> bool:
    """Функция проверяет доступность необходимых переменных окружения."""
    return all([BOT_TOKEN])


def check_db_file() -> bool:
    """Функция проверяет доступность файла БД."""
    return os.path.exists(DB_FILENAME)


if __name__ == '__main__':
    if not check_environment_variables():
        sys.exit('Проверьте наличие необходимых переменных окружения!')

    if not check_db_file():
        sys.exit('Проверьте наличие файла БД!')
    try:
        start_bot()
    except Exception:
        logger.exception('Ошибка при старте бота')
