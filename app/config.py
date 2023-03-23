import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Получаем токен бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Параметры для работы с SQL БД
# Запрос получает из базы расчетное время до ближайших поездов
DB_NAME = 'schedule'
DB_FILENAME = DB_NAME + '.sqlite3'
SQL_QUERY = f'''
    SELECT
      from_station,
      to_station, 
      strftime(
        '%H:%M:%S', 
        time(
          strftime('%s', departure_time) - strftime('%s', 'now', 'localtime'), 
          'unixepoch'
        )
      ) AS time_to_train
    FROM 
      {DB_NAME} 
    WHERE 
      from_station = ? 
      AND to_station = ? 
      AND is_weekend IS ? 
      AND departure_time > time('now', 'localtime') 
    LIMIT 
      2;
'''

# Задаем постоянные для работы бота

# Клавиатура для Telegram бота для выбора станции отправления
STATIONS_KEYBOARD = [
    [InlineKeyboardButton('Космонавтов', callback_data='Космонавтов')],
    [InlineKeyboardButton('Уралмаш', callback_data='Уралмаш')],
    [InlineKeyboardButton('Машиностроителей', callback_data='Машиностроителей')],
    [InlineKeyboardButton('Уральская', callback_data='Уральская')],
    [InlineKeyboardButton('Динамо', callback_data='Динамо')],
    [InlineKeyboardButton('Площадь 1905г', callback_data='Площадь 1905г')],
    [InlineKeyboardButton('Геологическая', callback_data='Геологическая')],
    [InlineKeyboardButton('Чкаловская', callback_data='Чкаловская')],
    [InlineKeyboardButton('Ботаническая', callback_data='Ботаническая')],
]
STATIONS_REPLY_MARKUP = InlineKeyboardMarkup(STATIONS_KEYBOARD)

# Клавиатура для конечных станций (только одно направление движения поездов)
TO_BOTANICHESKAYA = InlineKeyboardButton(
    'На Ботаническую',
    callback_data='Ботаническая'
)
TO_KOSMONAVTOV = InlineKeyboardButton(
    'На Космонавтов',
    callback_data='Космонавтов'
)
END_STATIONS_KEYBOARD = {
    'Космонавтов': TO_BOTANICHESKAYA,
    'Ботаническая': TO_KOSMONAVTOV,
}

HELP_TEXT = (
    'Бот показывает время до ближайшего поезда в метро Екатеринбурга.\n'
    'Выбери нужную станцию из списка командой /stations, а затем направление.'
)
