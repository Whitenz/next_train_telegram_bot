import logging
from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings

logger = logging.getLogger(__name__)


def write_log(func: Callable) -> Callable:
    """
    Функция-декоратор для логгирования действий пользователя при вызове
     обработчиков бота.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot_user = update.effective_user
        if update.callback_query:
            command = update.callback_query.data
        else:
            command = update.message.text
        logger_kwargs = {
            'id': bot_user.id if bot_user else None,
            'first_name': bot_user.first_name if bot_user else None,
            'command': command}
        logger.info(settings.LOGGER_TEXT.format(**logger_kwargs))
        return await func(update, context)
    return wrapper
