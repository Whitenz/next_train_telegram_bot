import typing as t

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from . import (
    bot_commands,
    handlers,
)
from .config import settings

COMMAND_HANDLERS = {
    bot_commands.START: handlers.start,
    bot_commands.HELP: handlers.help_handler,
    bot_commands.FAVORITES: handlers.favorites,
    bot_commands.CLEAR_FAVORITES: handlers.clear_favorites,
    # /broadcast не регистрируется здесь: команда является entry point
    # BROADCAST_CONVERSATION_HANDLER, а в группе 0 срабатывает только первый
    # совпавший обработчик — дубль похоронил бы диалог рассылки.
}


def register_handlers(application: Application[t.Any, t.Any, t.Any, t.Any, t.Any, t.Any]) -> None:
    """Регистрирует обработчики команд и диалогов в приложении бота."""
    for command, callback in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command, callback))
    application.add_handler(
        CommandHandler(
            bot_commands.DOWNLOAD_LOG,
            handlers.download_log,
            filters.User(settings.DEVELOPER_TG_ID),
        ),
    )
    application.add_handler(handlers.CONVERSATION_HANDLER)
    application.add_handler(handlers.BROADCAST_CONVERSATION_HANDLER)
    application.add_handler(MessageHandler(filters.ALL, handlers.wrong_command))
    application.add_error_handler(handlers.error_handler)


def start_bot() -> None:
    """Главная функция, стартующая бота."""
    application = ApplicationBuilder().token(settings.BOT_TOKEN).build()
    register_handlers(application)
    application.run_polling()
