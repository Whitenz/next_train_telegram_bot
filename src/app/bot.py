from warnings import filterwarnings

from telegram.ext import (ApplicationBuilder, CallbackQueryHandler, CommandHandler,
                          ConversationHandler, MessageHandler, filters)
from telegram.warnings import PTBUserWarning

from .config import BOT_TOKEN, CHOICE_DIRECTION, CONVERSATION_TIMEOUT, FINAL_STAGE
from .handlers import (clear_favorites, complete_conv, directions, favorites,
                       help_handler, start, stations, timeout, wrong_command)
from .messages import (ADD_FAVORITE_COMMAND, CLEAR_FAVORITES_COMMAND, FAVORITES_COMMAND,
                       HELP_COMMAND, SCHEDULE_COMMAND, START_COMMAND)

filterwarnings(action='ignore',
               message=r'.*CallbackQueryHandler',
               category=PTBUserWarning)

COMMAND_HANDLERS = {
    START_COMMAND: start,
    HELP_COMMAND: help_handler,
    FAVORITES_COMMAND: favorites,
    CLEAR_FAVORITES_COMMAND: clear_favorites
}


def start_bot() -> None:
    """Главная функция, стартующая бота."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    for command, callback in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(command, callback))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler((SCHEDULE_COMMAND, ADD_FAVORITE_COMMAND), stations)
        ],
        states={
            CHOICE_DIRECTION: [CallbackQueryHandler(directions)],
            FINAL_STAGE: [CallbackQueryHandler(complete_conv)],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, timeout),
                CallbackQueryHandler(timeout)
            ]
        },
        fallbacks=[MessageHandler(filters.ALL, wrong_command)],
        conversation_timeout=CONVERSATION_TIMEOUT
    )
    application.add_handler(conv_handler)

    application.add_handler(MessageHandler(filters.ALL, wrong_command))

    application.run_polling()
