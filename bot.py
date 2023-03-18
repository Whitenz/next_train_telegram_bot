#!/usr/bin/env python

import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from services import get_schedule

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get env
load_dotenv()

# Set constants
BOT_TOKEN = os.getenv('BOT_TOKEN')
STATIONS_KEYBOARD = [
    [InlineKeyboardButton("Космонавтов", callback_data="kosmonavtov")],
    [InlineKeyboardButton("Уралмаш", callback_data="uralmash")],
    [InlineKeyboardButton("Машиностроителей", callback_data="mashinostroitelej")],
    [InlineKeyboardButton("Уральская", callback_data="uralskaya")],
    [InlineKeyboardButton("Динамо", callback_data="dinamo")],
    [InlineKeyboardButton("Площадь 1905г", callback_data="ploshad_1905")],
    [InlineKeyboardButton("Геологическая", callback_data="geologicheskay")],
    [InlineKeyboardButton("Чкаловская", callback_data="chkalovskaya")],
    [InlineKeyboardButton("Ботаническая", callback_data="botanicheskaya")],
]
STATIONS_REPLY_MARKUP = InlineKeyboardMarkup(STATIONS_KEYBOARD)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    text = (f'Привет {user.mention_html(user.first_name)}!\n'
            'Бот показывает время до ближайшего поезда на выбранной станции.'
            'Выбери нужную из списка ниже, а затем направление')
    await update.message.reply_html(text)
    await update.message.reply_text('Выбери станцию:',
                                    reply_markup=STATIONS_REPLY_MARKUP)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    message = 'Бот отправляет время до ближайшего поезда командой /schedule'
    await update.message.reply_text(message)


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    schedule_info = get_schedule()
    closest_train = schedule_info[0][0]
    message = f'Следующий поезд через {closest_train} (ч:мин:с)'
    await update.message.reply_text(message)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("schedule", schedule))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
