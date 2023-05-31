from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from app import commands, handlers
from app.config import settings

COMMAND_HANDLERS = {
    commands.START: handlers.start,
    commands.HELP: handlers.help_handler,
    commands.FAVORITES: handlers.favorites,
    commands.CLEAR_FAVORITES: handlers.clear_favorites
}


def start_bot() -> None:
    """Главная функция, стартующая бота."""
    application = ApplicationBuilder().token(settings.BOT_TOKEN).build()

    for command, callback in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command, callback))

    application.add_handler(handlers.CONVERSATION_HANDLER)
    application.add_handler(MessageHandler(filters.ALL, handlers.wrong_command))
    application.add_error_handler(handlers.error_handler)
    application.run_polling()
