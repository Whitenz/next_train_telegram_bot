from warnings import filterwarnings

from telegram.ext import (ApplicationBuilder, CallbackQueryHandler, CommandHandler,
                          ConversationHandler, MessageHandler, filters)
from telegram.warnings import PTBUserWarning

from app import commands, handlers
from app.config import settings

filterwarnings(action='ignore',
               message=r'.*CallbackQueryHandler',
               category=PTBUserWarning)

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

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                (commands.SCHEDULE, commands.ADD_FAVORITE), handlers.stations
            )
        ],
        states={
            settings.CHOICE_DIRECTION: [CallbackQueryHandler(handlers.directions)],
            settings.FINAL_STAGE: [CallbackQueryHandler(handlers.complete_conv)],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, handlers.timeout),
                CallbackQueryHandler(handlers.timeout)
            ]
        },
        fallbacks=[MessageHandler(filters.ALL, handlers.wrong_command)],
        conversation_timeout=settings.CONVERSATION_TIMEOUT
    )
    application.add_handler(conv_handler)

    application.add_handler(MessageHandler(filters.ALL, handlers.wrong_command))

    application.run_polling()
