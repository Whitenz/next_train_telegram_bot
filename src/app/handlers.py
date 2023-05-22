from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from .config import settings
from .db import (STATIONS_DICT, delete_favorites_in_db, favorites_limited,
                 insert_favorite_to_db, insert_user_to_db, select_favorites_from_db,
                 select_schedule_from_db)
from .decorators import write_log
from .keyboards import (DIRECTION_REPLY_MARKUP, END_STATION_DIRECTION,
                        STATIONS_REPLY_MARKUP)
from .messages import (ADD_FAVORITE_COMMAND, ADD_FAVORITE_TEXT, CHOICE_DIRECTION_TEXT,
                       CHOICE_STATION_TEXT, CLEAR_FAVORITES_TEXT,
                       CLOSEST_TIME_TRAIN_TEXT, CONVERSATION_TIMEOUT_TEXT,
                       DIRECTION_TRAIN_TEXT, FAVORITE_EXISTS_TEXT,
                       FAVORITES_LIMIT_REACHED_TEXT, HELP_TEXT, LAST_TIME_TRAIN_TEXT,
                       METRO_IS_CLOSED_TEXT, NEXT_TIME_TRAIN_TEXT, NONE_TRAIN_TEXT,
                       SCHEDULE_COMMAND, START_TEXT, WRONG_COMMAND_TEXT)
from .utils import metro_is_closed


@write_log
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /start. Отправляет приветственное сообщение."""
    bot_user = update.effective_user
    if bot_user:
        text = START_TEXT.format(bot_user.first_name) + '\n\n' + HELP_TEXT
        await insert_user_to_db(bot_user)
        await update.message.reply_text(text)
    else:
        await wrong_command(update, context)


@write_log
async def help_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /help. Отправляет справочное сообщение."""
    await update.message.reply_text(HELP_TEXT)


@write_log
async def stations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команд /schedule и /add_favorite.
    Начало диалога. Отправляет список станций метрополитена в виде кнопок.
    Если получена команда 'schedule' и метрополитен открыт, то отправляет
     список станций.
    Если получена команда 'add_favorite' и список избранного пользователя не
     полон, то также отправляет список станций.
    """
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
        return settings.CHOICE_DIRECTION
    return ConversationHandler.END


@write_log
async def directions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Этап диалога для выбора направления движения поездов."""
    query = update.callback_query
    await query.answer()
    from_station_id = int(query.data)
    command = context.chat_data.get('command')

    if to_station_id := END_STATION_DIRECTION.get(from_station_id):
        if SCHEDULE_COMMAND in command:
            await _send_time_to_train(update, from_station_id, to_station_id)
        if ADD_FAVORITE_COMMAND in command:
            await _save_favorite(update, from_station_id, to_station_id)
        context.chat_data.clear()
        return ConversationHandler.END

    context.chat_data['from_station_id'] = from_station_id
    await query.edit_message_text(text=CHOICE_DIRECTION_TEXT,
                                  reply_markup=DIRECTION_REPLY_MARKUP)
    return settings.FINAL_STAGE


@write_log
async def complete_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Заключительный этап диалога команд /schedule и /add_favorite.
    Если была получена команда /schedule, то пользователю будет отправлено
     время до ближайших поездов.
    Если получена команда /add_favorite, то сохраняет избранным маршрут в БД.
    """
    query = update.callback_query
    await query.answer()
    command = context.chat_data.get('command')
    from_station_id = context.chat_data.get('from_station_id')
    to_station_id = int(query.data)
    if SCHEDULE_COMMAND in command:
        await _send_time_to_train(update, from_station_id, to_station_id)
    if ADD_FAVORITE_COMMAND in command:
        await _save_favorite(update, from_station_id, to_station_id)
    context.chat_data.clear()
    return ConversationHandler.END


@write_log
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
        text = '\n\n'.join(
            [await get_text_with_time_to_train(favorite.from_station_id,
                                               favorite.to_station_id)
             for favorite in user_favorites]
        )
    else:
        text = CLEAR_FAVORITES_TEXT
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@write_log
async def clear_favorites(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /favorites.
    Удаляет из БД все избранные маршруты пользователя.
    """
    id_bot_user = update.message.from_user.id
    await delete_favorites_in_db(id_bot_user)
    await update.message.reply_text(CLEAR_FAVORITES_TEXT)


@write_log
async def wrong_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик ошибочных команд.
    Функция обрабатывает все сообщения и команды, если бот их не должен
     обрабатывать в данный момент.
    """
    await update.message.reply_text(WRONG_COMMAND_TEXT)


async def _send_time_to_train(update: Update,
                              from_station_id: int,
                              to_station_id: int) -> None:
    """Функция отправляет пользователю время до ближайших поездов."""
    query = update.callback_query
    text = await get_text_with_time_to_train(from_station_id, to_station_id)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def _save_favorite(update: Update,
                         from_station_id: int,
                         to_station_id: int) -> None:
    """Функция сохраняет маршрут в БД и отправляет ответ пользователю."""
    query = update.callback_query
    id_bot_user = query.from_user.id
    new_favorite = await insert_favorite_to_db(id_bot_user,
                                               from_station_id,
                                               to_station_id)
    if new_favorite:
        text = ADD_FAVORITE_TEXT.format(direction=new_favorite.direction)
    else:
        text = FAVORITE_EXISTS_TEXT
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def timeout(_: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик таймаута диалога.
    Функция вызывается, если пользователь не ответил в заданное время находясь
     в диалоге.
    """
    if bot_message := context.chat_data.pop('bot_message', None):
        await bot_message.edit_text(CONVERSATION_TIMEOUT_TEXT)


async def get_text_with_time_to_train(from_station_id: int, to_station_id: int) -> str:
    schedules = await select_schedule_from_db(from_station_id, to_station_id)

    if schedules:
        text = DIRECTION_TRAIN_TEXT.format(direction=schedules[0].direction) + '\n\n'

        if len(schedules) == 1:
            return text + LAST_TIME_TRAIN_TEXT.format(
                time_to_train=schedules[0].time_to_train.strftime('%M:%S')
            )

        text = text + CLOSEST_TIME_TRAIN_TEXT.format(
            time_to_train=schedules[0].time_to_train.strftime('%M:%S')
        )
        for schedule in schedules[1:settings.LIMIT_ROW + 1]:
            text = text + '\n' + NEXT_TIME_TRAIN_TEXT.format(
                time_to_train=schedule.time_to_train.strftime('%M:%S')
            )
        return text

    from_station_name = STATIONS_DICT.get(from_station_id)
    to_station_name = STATIONS_DICT.get(to_station_id)
    direction = f'{from_station_name} ➡ {to_station_name}'
    return DIRECTION_TRAIN_TEXT.format(direction=direction) + '\n\n' + NONE_TRAIN_TEXT
