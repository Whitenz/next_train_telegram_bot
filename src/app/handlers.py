import datetime as dt
import html
import json
import logging
import traceback
from warnings import filterwarnings

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from app import (
    commands,
    db,
    keyboards,
    messages,
)
from app.config import settings
from app.decorators import write_log
from app.stations import get_stations_dict
from app.utils import metro_is_closed

filterwarnings(
    action='ignore',
    message=r'.*CallbackQueryHandler',
    category=PTBUserWarning,
)

logger = logging.getLogger(__name__)


@write_log
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /start. Отправляет приветственное сообщение."""
    if update.effective_user is None or update.message is None:
        await wrong_command(update, context)
        return

    text = messages.START.format(update.effective_user.first_name) + '\n\n' + messages.HELP
    await db.insert_user(update.effective_user)
    await update.message.reply_text(text)


@write_log
async def help_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка команды /help. Отправляет справочное сообщение."""
    if update.message:
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
    if update.effective_user is None or update.message is None:
        await wrong_command(update, context)
        return ConversationHandler.END

    command = update.message.text or ""
    if commands.SCHEDULE in command and await metro_is_closed():
        await update.message.reply_text(messages.METRO_IS_CLOSED)
    elif commands.ADD_FAVORITE in command and await db.favorites_limited(update.effective_user):
        await update.message.reply_text(messages.FAVORITES_LIMIT_REACHED)
    else:
        bot_message = await update.message.reply_text(
            messages.CHOICE_STATION,
            reply_markup=keyboards.STATIONS_REPLY_MARKUP,
        )

        if context.chat_data is not None:
            context.chat_data["bot_message"] = bot_message
            context.chat_data["command"] = command

        return settings.CHOICE_DIRECTION

    return ConversationHandler.END


@write_log
async def directions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Этап диалога для выбора направления движения поездов."""
    if (query := update.callback_query) is None or context.chat_data is None:
        return ConversationHandler.END

    await query.answer()
    from_station_id = int(query.data or "-1")
    command = context.chat_data.get("command", "undefined")

    if to_station_id := keyboards.END_STATION_DIRECTION.get(from_station_id):
        if commands.SCHEDULE in command:
            await _send_time_to_train(update, from_station_id, to_station_id)
        if commands.ADD_FAVORITE in command:
            await _save_favorite(update, from_station_id, to_station_id)
        context.chat_data.clear()
        return ConversationHandler.END

    context.chat_data['from_station_id'] = from_station_id
    await query.edit_message_text(
        text=messages.CHOICE_DIRECTION,
        reply_markup=keyboards.DIRECTION_REPLY_MARKUP,
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
    if (query := update.callback_query) is None or context.chat_data is None:
        return ConversationHandler.END

    await query.answer()
    command = context.chat_data.get("command", "undefined")
    from_station_id = context.chat_data.get("from_station_id", -1)
    to_station_id = int(query.data or "-1")
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
    if update.effective_user is None or update.message is None:
        await wrong_command(update, context)
        return

    if await metro_is_closed():
        text = messages.METRO_IS_CLOSED
    elif user_favorites := await db.select_favorites(update.effective_user):
        favorite_texts = [
            await get_text_with_time_to_train(favorite.from_station_id, favorite.to_station_id)
            for favorite in user_favorites
        ]
        text = '\n\n'.join(favorite_texts)
    else:
        text = messages.CLEAR_FAVORITES

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@write_log
async def clear_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /favorites.
    Удаляет из БД все избранные маршруты пользователя.
    """
    if update.effective_user is None or update.message is None:
        await wrong_command(update, context)
        return

    await db.delete_favorites(update.effective_user)
    await update.message.reply_text(messages.CLEAR_FAVORITES)


@write_log
async def wrong_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик ошибочных команд.
    Функция обрабатывает все сообщения и команды, если бот их не должен
     обрабатывать в данный момент.
    """
    if update.message is not None:
        await update.message.reply_text(messages.WRONG)


@write_log
async def download_log(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    time = dt.datetime.now().strftime('%d%m%Y%H%M%S')
    filename = f'bot_{time}.log'
    await update.message.reply_document(settings.LOG_FILENAME, filename=filename)


async def _send_time_to_train(
        update: Update,
        from_station_id: int,
        to_station_id: int,
) -> None:
    """Функция отправляет пользователю время до ближайших поездов."""
    if (query := update.callback_query) is None:
        return

    text = await get_text_with_time_to_train(from_station_id, to_station_id)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)


async def _save_favorite(
        update: Update,
        from_station_id: int,
        to_station_id: int,
) -> None:
    """Функция сохраняет маршрут в БД и отправляет ответ пользователю."""
    if (query := update.callback_query) is None:
        return

    bot_user = query.from_user
    await db.insert_user(bot_user)
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
    if context.chat_data is not None and (bot_message := context.chat_data.pop("bot_message", None)):
        await bot_message.edit_text(messages.CONVERSATION_TIMEOUT)


async def get_text_with_time_to_train(from_station_id: int, to_station_id: int) -> str:
    schedules = await db.select_schedule(from_station_id, to_station_id)

    if not schedules:
        from_station_name = get_stations_dict().get(from_station_id)
        to_station_name = get_stations_dict().get(to_station_id)
        direction = f'{from_station_name} ➡ {to_station_name}'
        return messages.DIRECTION_TRAIN.format(direction=direction) + '\n\n' + messages.NONE_TRAIN

    text = messages.DIRECTION_TRAIN.format(direction=schedules[0].direction) + '\n\n'
    if len(schedules) == 1:
        time_to_train = schedules[0].time_to_train.strftime('%M:%S')
        return text + messages.LAST_TIME_TRAIN.format(time_to_train=time_to_train)

    text += messages.CLOSEST_TIME_TRAIN.format(time_to_train=schedules[0].time_to_train.strftime('%M:%S'))
    for schedule in schedules[1:settings.LIMIT_ROW + 1]:
        text += '\n' + messages.NEXT_TIME_TRAIN.format(time_to_train=schedule.time_to_train.strftime('%M:%S'))
    return text


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик логирует ошибку и отправляет уведомление разработчику в телеграмм."""
    if context.error is None:
        return

    logger.error("Исключение при обработке объекта update:", exc_info=context.error)
    traceback_string = ''.join(traceback.format_exception(None, context.error, context.error.__traceback__))
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message_kwargs = {
        'update': html.escape(json.dumps(update_str, indent=2, ensure_ascii=False)),
        'chat_data': html.escape(str(context.chat_data)),
        'user_data': html.escape(str(context.user_data)),
        'traceback_string': traceback_string,
    }
    text = messages.ERROR.format(**message_kwargs)
    await context.bot.send_message(chat_id=settings.DEVELOPER_TG_ID, text=text, parse_mode=ParseMode.HTML)


CONVERSATION_HANDLER = ConversationHandler(
    entry_points=[
        CommandHandler((commands.SCHEDULE, commands.ADD_FAVORITE), stations),
    ],
    states={
        settings.CHOICE_DIRECTION: [CallbackQueryHandler(directions)],
        settings.FINAL_STAGE: [CallbackQueryHandler(complete_conv)],
        ConversationHandler.TIMEOUT: [
            MessageHandler(filters.ALL, timeout),
            CallbackQueryHandler(timeout),
        ],
    },
    fallbacks=[MessageHandler(filters.ALL, wrong_command)],
    conversation_timeout=settings.CONVERSATION_TIMEOUT,
)
