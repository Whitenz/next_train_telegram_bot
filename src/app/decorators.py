import logging
from functools import wraps
import typing as t

from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings

logger = logging.getLogger(__name__)

F = t.TypeVar('F', bound=t.Callable[[Update, ContextTypes.DEFAULT_TYPE], t.Awaitable[t.Any]])


def write_log(func: F) -> F:
    """
    Функция-декоратор для логгирования действий пользователя при вызове
     обработчиков бота.
    """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> t.Awaitable[t.Any]:
        bot_user = update.effective_user
        if update.callback_query:
            command = update.callback_query.data
        elif update.message:
            command = update.message.text
        else:
            command = "undefined"
        logger_kwargs = {
            'id': bot_user.id if bot_user else None,
            'first_name': bot_user.first_name if bot_user else None,
            'command': command,
        }
        logger.info(settings.LOGGER_TEXT.format(**logger_kwargs))
        return await func(update, context)

    return t.cast(F, wrapper)
