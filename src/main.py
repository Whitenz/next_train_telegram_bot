import logging
import sys

from app.bot import start_bot
from app.config import BOT_TOKEN

logger = logging.getLogger(__name__)


def check_environment_variables() -> bool:
    """Функция проверяет доступность необходимых переменных окружения."""
    return all([BOT_TOKEN])


if __name__ == '__main__':
    if not check_environment_variables():
        sys.exit('Проверьте наличие необходимых переменных окружения!')

    try:
        start_bot()
    except Exception:
        logger.exception('Ошибка при старте бота')
