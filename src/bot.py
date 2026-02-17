from telegram.ext import (
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
    bot_commands.BROADCAST: handlers.broadcast,
}


def start_bot() -> None:
    """Главная функция, стартующая бота."""
    application = ApplicationBuilder().token(settings.BOT_TOKEN).build()
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
    application.run_polling()
