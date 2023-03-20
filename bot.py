#!/usr/bin/env python

import logging

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import (ApplicationBuilder,
                          CallbackQueryHandler,
                          CommandHandler,
                          ContextTypes,
                          ConversationHandler)

from config import (BOT_TOKEN,
                    END_STATIONS_KEYBOARD,
                    STATIONS,
                    STATIONS_REPLY_MARKUP,
                    HELP_TEXT)
from services import get_schedule

# Подключаем логгер
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CHOICE_DIRECTION, NEXT_TRAIN = range(3)


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
    await update.message.reply_text('Выбери станцию:',
                                    reply_markup=STATIONS_REPLY_MARKUP)
    return CHOICE_DIRECTION


async def directions(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> int:
    """Этап диалога для выбора направления движения поездов."""
    query = update.callback_query
    from_station = query.data
    context.chat_data['from_station'] = from_station
    # Ниже проверка на конечную станцию, т.к. тогда только одно направление
    if from_station in END_STATIONS_KEYBOARD:
        keyboard = [[END_STATIONS_KEYBOARD[from_station]]]
    else:
        keyboard = [[*END_STATIONS_KEYBOARD.values()]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(
        text="Выбери направление:", reply_markup=reply_markup
    )
    return NEXT_TRAIN


async def time_to_train(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """Заключительный этап диалога. Отправляет время до ближайших поездов."""
    query = update.callback_query
    to_station = query.data
    from_station = context.chat_data.get('from_station')
    schedule_info = get_schedule(from_station, to_station)
    closest_train = schedule_info[0][0]
    next_train = schedule_info[1][0]
    text = (f'{STATIONS.get(from_station)} --> {STATIONS.get(to_station)}:\n\n'
            f'ближайший поезд через {closest_train} (ч:мин:с)\n'
            f'следующий через {next_train} (ч:мин:с)')
    await query.answer()
    await query.edit_message_text(text)
    return ConversationHandler.END


def main() -> None:
    """Главная функция, стартующая бота."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("stations", stations)],
        states={
            CHOICE_DIRECTION: [CallbackQueryHandler(directions)],
            NEXT_TRAIN: [CallbackQueryHandler(time_to_train)],
        },
        fallbacks=[CommandHandler("stations", stations)],
    )
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
