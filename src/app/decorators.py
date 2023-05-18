import logging
from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from .config import LOGGER_TEXT

logger = logging.getLogger(__name__)


def write_log(func: Callable) -> Callable:
    """
    Функция-декоратор для логгирования действий пользователя при вызове
     обработчиков бота.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            command = update.callback_query.data
        else:
            command = update.message.text
        logger_kwargs = {'id_bot_user': update.effective_user.id,
                         'first_name': update.effective_user.first_name,
                         'command': command}
        logger.info(LOGGER_TEXT.format(**logger_kwargs))
        return await func(update, context)
    return wrapper
