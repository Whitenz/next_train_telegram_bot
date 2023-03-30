#!/usr/bin/env python
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (ApplicationBuilder,
                          CallbackQueryHandler,
                          CommandHandler,
                          ContextTypes,
                          ConversationHandler,
                          MessageHandler,
                          filters)

from config import (ADD_FAVORITES_COMMAND, BOT_TOKEN,
                    CHOICE_DIRECTION,
                    DIRECTION_REPLY_MARKUP,
                    END_STATION_DIRECTION,
                    ADD_FAVORITES_TO_DB,
                    GET_TIME_TO_TRAIN,
                    HELP_COMMAND, HELP_TEXT,
                    METRO_IS_CLOSED_TEXT,
                    SCHEDULE_COMMAND,
                    START_COMMAND, STATIONS_REPLY_MARKUP)
from services import (add_favorites_to_db,
                      get_schedule,
                      get_text_with_time_to_train,
                      metro_is_closed)

# Подключаем логгер
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение после команды /start."""
    user = update.effective_user.first_name
    await update.message.reply_text(f'Привет {user}!\n' + HELP_TEXT)


async def help_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение после команды /help."""
    await update.message.reply_text(HELP_TEXT)


async def stations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет список станций после команды /stations."""
    message = update.message
    if SCHEDULE_COMMAND in message.text and metro_is_closed():
        await update.message.reply_text(METRO_IS_CLOSED_TEXT)
        return ConversationHandler.END
    await update.message.reply_text('Выбери станцию:',
                                    reply_markup=STATIONS_REPLY_MARKUP)
    return CHOICE_DIRECTION


async def directions(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> int:
    """Этап диалога для выбора направления движения поездов."""
    query = update.callback_query
    from_station = query.data
    # Ниже проверка на конечную станцию, т.к. тогда только одно направление
    # и дальнейший выбор направления не нужен
    if from_station in END_STATION_DIRECTION:
        to_station = END_STATION_DIRECTION[from_station]
        schedule = await get_schedule(from_station, to_station)
        text = get_text_with_time_to_train(schedule)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    context.chat_data['from_station'] = from_station
    reply_markup = DIRECTION_REPLY_MARKUP
    await query.answer()
    await query.edit_message_text(text="Выбери направление:",
                                  reply_markup=reply_markup)
    return GET_TIME_TO_TRAIN


async def time_to_train(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """Заключительный этап диалога. Отправляет время до ближайших поездов."""
    query = update.callback_query
    from_station = context.chat_data.get('from_station')
    to_station = query.data
    schedule = await get_schedule(from_station, to_station)
    text = get_text_with_time_to_train(schedule)
    await query.answer()
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def add_favorites(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """Заключительный этап диалога. Отправляет статус записи в 'favorite'."""
    query = update.callback_query
    from_station = context.chat_data.get('from_station')
    to_station = query.data
    id_bot_user = query.from_user.id
    result = add_favorites_to_db(from_station, to_station, id_bot_user)
    await query.answer()
    await query.edit_message_text('test', parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def wrong_command(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> None:
    """Функция обрабатывает все сообщения и команды, если бот их не должен
     обрабатывать в данный момент. Находясь в ConversationHandler бот принимает
     только ввод с предложенных кнопок."""
    await update.message.reply_text(text='Некорректная команда')


def main() -> None:
    """Главная функция, стартующая бота."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler(START_COMMAND, start))
    application.add_handler(CommandHandler(HELP_COMMAND, help_command))
    schedule_handler = ConversationHandler(
        entry_points=[CommandHandler(SCHEDULE_COMMAND, stations)],
        states={
            CHOICE_DIRECTION: [CallbackQueryHandler(directions)],
            GET_TIME_TO_TRAIN: [CallbackQueryHandler(time_to_train)],
        },
        fallbacks=[MessageHandler(filters.ALL, wrong_command)],
    )
    add_favorites_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_FAVORITES_COMMAND, stations)],
        states={
            CHOICE_DIRECTION: [CallbackQueryHandler(directions)],
            ADD_FAVORITES_TO_DB: [CallbackQueryHandler(add_favorites)],
        },
        fallbacks=[MessageHandler(filters.ALL, wrong_command)],
    )
    application.add_handler(schedule_handler)
    application.add_handler(add_favorites_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
