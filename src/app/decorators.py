from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from .config import logger


def write_log(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.callback_query:
            command = update.callback_query.data
        else:
            command = update.message.text
        logger.info(
            f'Пользователь {update.effective_user.id} отправил команду "{command}"'
        )
        return await func(update, context)
    return wrapper
