from warnings import filterwarnings

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, ContextTypes, ConversationHandler,
                          MessageHandler, filters)
from telegram.warnings import PTBUserWarning

from .config import (BOT_TOKEN, CHOICE_DIRECTION, CONVERSATION_TIMEOUT,
                     FINAL_STAGE)
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
from .utils import (format_text_with_time_to_train, metro_is_closed,
                    write_to_log)

filterwarnings(action='ignore',
               message=r'.*CallbackQueryHandler',
               category=PTBUserWarning)


async def start(update: Update, _) -> None:
    """Обработка команды /start. Отправляет приветственное сообщение."""
    await write_to_log(update)
    bot_user = update.effective_user
    text = START_TEXT.format(bot_user.first_name) + '\n\n' + HELP_TEXT
    await insert_user_to_db(bot_user)
    await update.message.reply_text(text)


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /help. Отправляет справочное сообщение."""
    await write_to_log(update)
    await update.message.reply_text(HELP_TEXT)


async def stations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команд /schedule и /add_favorite.
    Начало диалога. Отправляет список станций метрополитена в виде кнопок.
    Если получена команда 'schedule' и метрополитен открыт, то отправляет
     список станций.
    Если получена команда 'add_favorite' и список избранного пользователя не
     полон, то также отправляет список станций.
    """
    await write_to_log(update)
    command = update.message.text
    id_bot_user = update.message.from_user.id
    if SCHEDULE_COMMAND in command and await metro_is_closed():
        await update.message.reply_text(METRO_IS_CLOSED_TEXT)
    elif ADD_FAVORITE_COMMAND in command and await favorites_limited(id_bot_user):
        await update.message.reply_text(FAVORITES_LIMIT_REACHED_TEXT)
    else:
        bot_message = await update.message.reply_text(
            CHOICE_STATION_TEXT, reply_markup=STATIONS_REPLY_MARKUP
        )
        context.chat_data['bot_message'] = bot_message
        context.chat_data['command'] = command
        return CHOICE_DIRECTION
    return ConversationHandler.END


async def directions(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> int:
    """Этап диалога для выбора направления движения поездов."""

    await write_to_log(update)
    query = update.callback_query
    await query.answer()
    from_station = query.data
    command = context.chat_data.get('command')

    if to_station := END_STATION_DIRECTION.get(from_station):
        if SCHEDULE_COMMAND in command:
            await send_time_to_train(update, from_station, to_station)
        if ADD_FAVORITE_COMMAND in command:
            await save_favorite(update, from_station, to_station)
        context.chat_data.clear()
        return ConversationHandler.END

    context.chat_data['from_station'] = from_station
    await query.edit_message_text(text=CHOICE_DIRECTION_TEXT,
                                  reply_markup=DIRECTION_REPLY_MARKUP)
    return FINAL_STAGE


async def complete_conv(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Заключительный этап диалога команд /schedule и /add_favorite.
    Если была получена команда /schedule, то пользователю будет отправлено
     время до ближайших поездов.
    Если получена команда /add_favorite, то сохраняет избранным маршрут в БД.
    """
    await write_to_log(update)
    query = update.callback_query
    await query.answer()
    command = context.chat_data.get('command')
    from_station = context.chat_data.get('from_station')
    to_station = query.data
    if SCHEDULE_COMMAND in command:
        await send_time_to_train(update, from_station, to_station)
    if ADD_FAVORITE_COMMAND in command:
        await save_favorite(update, from_station, to_station)
    context.chat_data.clear()
    return ConversationHandler.END


async def send_time_to_train(update: Update,
                             from_station: str,
                             to_station: str) -> None:
    """Функция отправляет пользователю время до ближайших поездов."""
    query = update.callback_query
    schedule = await select_schedule(from_station, to_station)
    text = await format_text_with_time_to_train(schedule)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def save_favorite(update: Update,
                        from_station: str,
                        to_station: str) -> None:
    """Функция сохраняет маршрут в БД и отправляет ответ пользователю."""
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
    await write_to_log(update)
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
    await write_to_log(update)
    id_bot_user = update.message.from_user.id
    await delete_favorites_in_db(id_bot_user)
    await update.message.reply_text(CLEAR_FAVORITES_TEXT)


async def wrong_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик ошибочных команд.
    Функция обрабатывает все сообщения и команды, если бот их не должен
     обрабатывать в данный момент.
    """
    await write_to_log(update)
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
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler((SCHEDULE_COMMAND, ADD_FAVORITE_COMMAND),
                                     stations)],
        states={
            CHOICE_DIRECTION: [CallbackQueryHandler(directions)],
            FINAL_STAGE: [CallbackQueryHandler(complete_conv)],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, timeout),
                                          CallbackQueryHandler(timeout)]
        },
        fallbacks=[MessageHandler(filters.ALL, wrong_command)],
        conversation_timeout=CONVERSATION_TIMEOUT
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler(FAVORITES_COMMAND, favorites))
    application.add_handler(CommandHandler(CLEAR_FAVORITES_COMMAND,
                                           clear_favorites))
    application.add_handler(MessageHandler(filters.ALL, wrong_command))
    application.run_polling()
