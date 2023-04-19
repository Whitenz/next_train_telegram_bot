import logging

from telegram import Message, Update
from telegram.constants import ParseMode
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, ContextTypes, ConversationHandler,
                          MessageHandler, filters)

from .config import (BOT_TOKEN, CHOICE_DIRECTION, CONVERSATION_TIMEOUT,
                     GET_TIME_TO_TRAIN, NEW_FAVORITE)
from .db import (delete_favorites_in_db, favorites_limited,
                 insert_favorite_to_db, insert_user_to_db,
                 select_favorites_from_db, select_schedule)
from .keyboards import (DIRECTION_REPLY_MARKUP, END_STATION_DIRECTION,
                        STATIONS_REPLY_MARKUP)
from .messages import (ADD_FAVORITE_COMMAND, ADD_FAVORITES_TEXT,
                       CHOICE_DIRECTION_TEXT, CHOICE_STATION_TEXT,
                       CLEAR_FAVORITES_COMMAND, CLEAR_FAVORITES_TEXT,
                       CONVERSATION_TIMEOUT_TEXT, FAVORITES_COMMAND,
                       FAVORITES_LIMIT_REACHED_TEXT, HELP_COMMAND, HELP_TEXT,
                       METRO_IS_CLOSED_TEXT, SCHEDULE_COMMAND, START_COMMAND,
                       START_TEXT, WRONG_COMMAND_TEXT)
from .utils import format_text_with_time_to_train, metro_is_closed

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING
)
logger = logging.getLogger(__name__)


async def start(update: Update, _) -> None:
    """Обработка команды /start. Отправляет приветственное сообщение."""
    bot_user = update.effective_user
    text = START_TEXT.format(bot_user.first_name) + '\n\n' + HELP_TEXT
    await insert_user_to_db(bot_user)
    await update.message.reply_text(text)


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /help. Отправляет справочное сообщение."""
    await update.message.reply_text(HELP_TEXT)


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка команды /schedule. Начало диалога.
    Если метрополитен открыт, то отправляет пользователю список станций
    отправления поездов для получения времени до ближайшего поезда.
    """
    if await metro_is_closed():
        await update.message.reply_text(METRO_IS_CLOSED_TEXT)
        return ConversationHandler.END
    context.chat_data['bot_message'] = await stations(update)
    return CHOICE_DIRECTION


async def schedule_directions(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> int:
    """Этап диалога /schedule для выбора направления движения поездов."""
    query = update.callback_query
    await query.answer()
    from_station = query.data

    if from_station in END_STATION_DIRECTION:
        to_station = END_STATION_DIRECTION[from_station]
        await send_time_to_train(update, from_station, to_station)
        context.chat_data.clear()
        return ConversationHandler.END

    context.chat_data['from_station'] = from_station
    await query.edit_message_text(text=CHOICE_DIRECTION_TEXT,
                                  reply_markup=DIRECTION_REPLY_MARKUP)
    return GET_TIME_TO_TRAIN


async def time_to_train(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """Заключительный этап диалога /schedule. Отправляет время до поездов."""
    query = update.callback_query
    await query.answer()
    from_station = context.chat_data.get('from_station')
    to_station = query.data
    await send_time_to_train(update, from_station, to_station)
    context.chat_data.clear()
    return ConversationHandler.END


async def stations(update: Update) -> Message:
    """
    Отправляет список станций список станций метрополитена в форме кнопок.
    Возвращает объект Message - сообщение, которое бот отправил пользователю.
    """
    return await update.message.reply_text(CHOICE_STATION_TEXT,
                                           reply_markup=STATIONS_REPLY_MARKUP)


async def send_time_to_train(update: Update,
                             from_station: str,
                             to_station: str) -> None:
    query = update.callback_query
    schedule = await select_schedule(from_station, to_station)
    text = await format_text_with_time_to_train(schedule)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /add_favorite. Начало диалога.
    Если пользователь не достиг лимита записей в избранное, то отправляет
    список станций метрополитена для сохранения нового избранного маршрута.
    """
    id_bot_user = update.message.from_user.id
    if await favorites_limited(id_bot_user):
        await update.message.reply_text(FAVORITES_LIMIT_REACHED_TEXT)
        return ConversationHandler.END
    context.chat_data['bot_message'] = await stations(update)
    return CHOICE_DIRECTION


async def favorite_directions(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> int:
    """Этап диалога /add_favorite для выбора направления движения поездов."""
    query = update.callback_query
    await query.answer()
    from_station = query.data

    if from_station in END_STATION_DIRECTION:
        to_station = END_STATION_DIRECTION[from_station]
        await save_favorite(update, from_station, to_station)
        context.chat_data.clear()
        return ConversationHandler.END

    context.chat_data['from_station'] = from_station
    await query.edit_message_text(text=CHOICE_DIRECTION_TEXT,
                                  reply_markup=DIRECTION_REPLY_MARKUP)
    return NEW_FAVORITE


async def new_favorite(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Заключительный этап диалога /add_favorite.
    Добавляет в список избранного пользователя новый маршрут.
    """
    query = update.callback_query
    await query.answer()
    from_station = context.chat_data.get('from_station')
    to_station = query.data
    await save_favorite(update, from_station, to_station)
    context.chat_data.clear()
    return ConversationHandler.END


async def save_favorite(update: Update,
                        from_station: str,
                        to_station: str) -> None:
    """Функция проводить запись в БД и отправляет ответ пользователю."""
    query = update.callback_query
    id_bot_user = query.from_user.id
    text = ADD_FAVORITES_TEXT.format(from_station, to_station)
    await insert_favorite_to_db(id_bot_user, from_station, to_station)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def favorites(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /favorites.
    Отправляет время до ближайших поездов по избранным маршрутам пользователя.
    """
    if await metro_is_closed():
        await update.message.reply_text(METRO_IS_CLOSED_TEXT)
        return
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
    """
    Обработчик команды /favorites.
    Удаляет из БД все избранные маршруты пользователя.
    """
    id_bot_user = update.message.from_user.id
    await delete_favorites_in_db(id_bot_user)
    await update.message.reply_text(CLEAR_FAVORITES_TEXT)


async def wrong_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик ошибочных команд.
    Функция обрабатывает все сообщения и команды, если бот их не должен
     обрабатывать в данный момент.
    """
    await update.message.reply_text(WRONG_COMMAND_TEXT)


async def timeout(_: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик таймаута диалога.
    Функция вызывается, если пользователь не ответил в заданное время находясь
     в диалоге.
    """
    if bot_message := context.chat_data.pop('bot_message', None):
        await bot_message.edit_text(CONVERSATION_TIMEOUT_TEXT)


def start_bot() -> None:
    """Главная функция, стартующая бота."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler(START_COMMAND, start))
    application.add_handler(CommandHandler(HELP_COMMAND, help_command))
    shedule_handler = ConversationHandler(
        entry_points=[CommandHandler(SCHEDULE_COMMAND, schedule)],
        states={
            CHOICE_DIRECTION: [CallbackQueryHandler(schedule_directions)],
            GET_TIME_TO_TRAIN: [CallbackQueryHandler(time_to_train)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, timeout),
                                          CallbackQueryHandler(timeout)]
        },
        fallbacks=[MessageHandler(filters.ALL, wrong_command)],
        conversation_timeout=CONVERSATION_TIMEOUT
    )
    add_favorite_handler = ConversationHandler(
        entry_points=[CommandHandler(ADD_FAVORITE_COMMAND, add_favorite)],
        states={
            CHOICE_DIRECTION: [CallbackQueryHandler(favorite_directions)],
            NEW_FAVORITE: [CallbackQueryHandler(new_favorite)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, timeout),
                                          CallbackQueryHandler(timeout)]
        },
        fallbacks=[MessageHandler(filters.ALL, wrong_command)],
        conversation_timeout=CONVERSATION_TIMEOUT
    )
    application.add_handler(shedule_handler)
    application.add_handler(add_favorite_handler)
    application.add_handler(CommandHandler(FAVORITES_COMMAND, favorites))
    application.add_handler(CommandHandler(CLEAR_FAVORITES_COMMAND,
                                           clear_favorites))
    application.add_handler(MessageHandler(filters.ALL, wrong_command))
    application.run_polling()
