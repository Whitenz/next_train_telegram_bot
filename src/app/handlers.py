from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from app import commands, db, keyboards, messages
from app.config import settings
from app.decorators import write_log
from app.utils import metro_is_closed


@write_log
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /start. Отправляет приветственное сообщение."""
    bot_user = update.effective_user
    if bot_user:
        text = messages.START.format(bot_user.first_name) + '\n\n' + messages.HELP
        await db.insert_user(bot_user)
        await update.message.reply_text(text)
    else:
        await wrong_command(update, context)


@write_log
async def help_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /help. Отправляет справочное сообщение."""
    await update.message.reply_text(messages.HELP)


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
    bot_user = update.effective_user
    if commands.SCHEDULE in command and await metro_is_closed():
        await update.message.reply_text(messages.METRO_IS_CLOSED)
    elif commands.ADD_FAVORITE in command and await db.favorites_limited(bot_user):
        await update.message.reply_text(messages.FAVORITES_LIMIT_REACHED)
    else:
        bot_message = await update.message.reply_text(
            messages.CHOICE_STATION, reply_markup=keyboards.STATIONS_REPLY_MARKUP
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

    if to_station_id := keyboards.END_STATION_DIRECTION.get(from_station_id):
        if commands.SCHEDULE in command:
            await _send_time_to_train(update, from_station_id, to_station_id)
        if commands.ADD_FAVORITE in command:
            await _save_favorite(update, from_station_id, to_station_id)
        context.chat_data.clear()
        return ConversationHandler.END

    context.chat_data['from_station_id'] = from_station_id
    await query.edit_message_text(
        text=messages.CHOICE_DIRECTION, reply_markup=keyboards.DIRECTION_REPLY_MARKUP
    )
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
    if commands.SCHEDULE in command:
        await _send_time_to_train(update, from_station_id, to_station_id)
    if commands.ADD_FAVORITE in command:
        await _save_favorite(update, from_station_id, to_station_id)
    context.chat_data.clear()
    return ConversationHandler.END


@write_log
async def favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /favorites.
    Отправляет время до ближайших поездов по избранным маршрутам пользователя.
    """
    if await metro_is_closed():
        await update.message.reply_text(messages.METRO_IS_CLOSED)
        return

    bot_user = update.effective_user
    if bot_user:
        await db.insert_user(bot_user)
        if user_favorites := await db.select_favorites(bot_user):
            text = '\n\n'.join(
                [await get_text_with_time_to_train(favorite.from_station_id,
                                                   favorite.to_station_id)
                 for favorite in user_favorites]
            )
        else:
            text = messages.CLEAR_FAVORITES
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        await wrong_command(update, context)


@write_log
async def clear_favorites(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /favorites.
    Удаляет из БД все избранные маршруты пользователя.
    """
    bot_user = update.effective_user
    await db.delete_favorites(bot_user)
    await update.message.reply_text(messages.CLEAR_FAVORITES)


@write_log
async def wrong_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик ошибочных команд.
    Функция обрабатывает все сообщения и команды, если бот их не должен
     обрабатывать в данный момент.
    """
    await update.message.reply_text(messages.WRONG)


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
    bot_user = query.from_user
    new_favorite = await db.insert_favorite(bot_user, from_station_id, to_station_id)
    if new_favorite:
        text = messages.ADD_FAVORITE.format(direction=new_favorite.direction)
    else:
        text = messages.FAVORITE_EXISTS
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def timeout(_: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик таймаута диалога.
    Функция вызывается, если пользователь не ответил в заданное время находясь
     в диалоге.
    """
    if bot_message := context.chat_data.pop('bot_message', None):
        await bot_message.edit_text(messages.CONVERSATION_TIMEOUT)


async def get_text_with_time_to_train(from_station_id: int, to_station_id: int) -> str:
    schedules = await db.select_schedule(from_station_id, to_station_id)

    if schedules:
        text = messages.DIRECTION_TRAIN.format(
            direction=schedules[0].direction) + '\n\n'

        if len(schedules) == 1:
            return text + messages.LAST_TIME_TRAIN.format(
                time_to_train=schedules[0].time_to_train.strftime('%M:%S')
            )

        text = text + messages.CLOSEST_TIME_TRAIN.format(
            time_to_train=schedules[0].time_to_train.strftime('%M:%S')
        )
        for schedule in schedules[1:settings.LIMIT_ROW + 1]:
            text = text + '\n' + messages.NEXT_TIME_TRAIN.format(
                time_to_train=schedule.time_to_train.strftime('%M:%S')
            )
        return text

    from_station_name = db.STATIONS_DICT.get(from_station_id)
    to_station_name = db.STATIONS_DICT.get(to_station_id)
    direction = f'{from_station_name} ➡ {to_station_name}'
    return (
        messages.DIRECTION_TRAIN.format(direction=direction)
        + '\n\n'
        + messages.NONE_TRAIN
    )
