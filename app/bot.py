#!/usr/bin/env python
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (ApplicationBuilder,
                          CallbackQueryHandler,
                          CommandHandler,
                          ContextTypes,
                          ConversationHandler,
                          filters,
                          MessageHandler)

from config import (ADD_FAVORITES_TEXT,
                    BOT_TOKEN,
                    CHOICE_DIRECTION,
                    CHOICE_DIRECTION_TEXT, CHOICE_STATION_TEXT,
                    CLEAR_FAVORITES_COMMAND,
                    CLEAR_FAVORITES_TEXT,
                    DIRECTION_REPLY_MARKUP,
                    END_STATION_DIRECTION, FAVORITES_COMMAND,
                    FAVORITES_LIMIT_REACHED_TEXT,
                    HELP_COMMAND,
                    HELP_TEXT, METRO_IS_CLOSED_TEXT,
                    SCHEDULE_COMMAND,
                    START_COMMAND,
                    START_TEXT,
                    STATIONS_REPLY_MARKUP,
                    GET_TIME_TO_TRAIN,
                    WRONG_COMMAND_TEXT)
from services import (insert_favorite_to_db,
                      delete_favorites_in_db,
                      favorites_limited, select_favorites_from_db,
                      select_schedule,
                      format_text_with_time_to_train,
                      metro_is_closed)

# Подключаем логгер
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, _) -> None:
    """Отправляет приветственное сообщение после команды /start."""
    bot_user = update.effective_user
    text = START_TEXT.format(bot_user.first_name) + '\n\n' + HELP_TEXT
    await update.message.reply_text(text)


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справочное сообщение после команды /help."""
    await update.message.reply_text(HELP_TEXT)


async def stations(update: Update,
                   _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет список станций список станций метрополитена в форме кнопок.
    """
    await update.message.reply_text(CHOICE_STATION_TEXT,
                                    reply_markup=STATIONS_REPLY_MARKUP)


async def directions(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> int:
    """Этап диалога для выбора направления движения поездов."""
    query = update.callback_query
    await query.answer()
    from_station = query.data
    context.chat_data['from_station'] = from_station

    if from_station in END_STATION_DIRECTION:
        to_station = END_STATION_DIRECTION[from_station]
        await send_time_to_train(update, context, from_station, to_station)
        return ConversationHandler.END

    await query.edit_message_text(text=CHOICE_DIRECTION_TEXT,
                                  reply_markup=DIRECTION_REPLY_MARKUP)
    return GET_TIME_TO_TRAIN


async def time_to_train(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """Заключительный этап диалога. Отправляет время до ближайших поездов."""
    query = update.callback_query
    await query.answer()
    from_station = context.chat_data.get('from_station')
    to_station = query.data
    await send_time_to_train(update, context, from_station, to_station)
    return ConversationHandler.END


async def send_time_to_train(update: Update,
                             _: ContextTypes.DEFAULT_TYPE,
                             from_station: str,
                             to_station: str) -> None:
    query = update.callback_query
    schedule = await select_schedule(from_station, to_station)
    text = await format_text_with_time_to_train(schedule)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def save_favorite(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """Добавляет в таблицу 'favorite' избранный маршрут пользователя."""
    query = update.callback_query
    from_station = context.chat_data.get('from_station')
    to_station = query.data
    id_bot_user = query.from_user.id
    text = ADD_FAVORITES_TEXT.format(from_station, to_station)
    await insert_favorite_to_db(id_bot_user, from_station, to_station)
    await query.answer()
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def schedule(update: Update,
                   context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправляет список станций после команды /schedule. Начало диалога.
    """
    if await metro_is_closed():
        await update.message.reply_text(METRO_IS_CLOSED_TEXT)
        return ConversationHandler.END
    await stations(update, context)
    return CHOICE_DIRECTION


async def add_favorite_start(update: Update,
                             _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправляет список станций после команды /add_favorite. Начало диалога.
    """
    id_user = update.message.from_user.id
    if await favorites_limited(id_user):
        await update.message.reply_text(FAVORITES_LIMIT_REACHED_TEXT)
        return ConversationHandler.END

    await update.message.reply_text(CHOICE_STATION_TEXT,
                                    reply_markup=STATIONS_REPLY_MARKUP)
    return CHOICE_DIRECTION


async def favorites(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет информацию по избранным маршрутам после команды /favorites."""
    id_bot_user = update.message.from_user.id
    if user_favorites := await select_favorites_from_db(id_bot_user):
        schedules = [await select_schedule(*favorite)
                     for favorite in user_favorites]
        texts = [await format_text_with_time_to_train(schedule)
                 for schedule in schedules]
        text = '\n\n'.join(texts)
    else:
        text = CLEAR_FAVORITES_TEXT
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def clear_favorites(update: Update,
                          _: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет из БД все избранные маршруты пользователя."""
    id_bot_user = update.message.from_user.id
    await delete_favorites_in_db(id_bot_user)
    await update.message.reply_text(CLEAR_FAVORITES_TEXT)


async def wrong_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Функция обрабатывает все сообщения и команды, если бот их не должен
     обрабатывать в данный момент. Находясь в ConversationHandler бот принимает
     только ввод с предложенных кнопок."""
    await update.message.delete()
    await update.message.reply_text(WRONG_COMMAND_TEXT)


def main() -> None:
    """Главная функция, стартующая бота."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler(START_COMMAND, start))
    application.add_handler(CommandHandler(HELP_COMMAND, help_command))
    shedule_handler = ConversationHandler(
        entry_points=[CommandHandler(SCHEDULE_COMMAND, schedule)],
        states={
            CHOICE_DIRECTION: [CallbackQueryHandler(directions)],
            GET_TIME_TO_TRAIN: [CallbackQueryHandler(time_to_train)],
        },
        fallbacks=[MessageHandler(filters.ALL, wrong_command)],
    )
    application.add_handler(shedule_handler)
    # add_favorite_handler = ...
    # application.add_handler(add_favorite_handler)
    application.add_handler(CommandHandler(FAVORITES_COMMAND, favorites))
    application.add_handler(CommandHandler(CLEAR_FAVORITES_COMMAND,
                                           clear_favorites))
    application.run_polling()


if __name__ == "__main__":
    main()
