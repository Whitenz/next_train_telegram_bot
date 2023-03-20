import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Получаем токен бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# SQL параметры
# Запрос получает из базы расчетное время до ближайших двух поездов
DB_NAME = 'schedule'
SQL_QUERY = f'''
    SELECT 
      strftime(
        '%H:%M:%S', 
        time(
          strftime('%s', departure_time) - strftime('%s', 'now', 'localtime'), 
          'unixepoch'
        )
      ) 
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
STATIONS = {
    'kosmonavtov': 'Космонавтов',
    'uralmash': 'Уралмаш',
    'mashinostroitelej': 'Машиностроителей',
    'uralskaya': 'Уральская',
    'dinamo': 'Динамо',
    'ploshad_1905': 'Площадь 1905г',
    'geologicheskaya': 'Геологическая',
    'chkalovskaya': 'Чкаловская',
    'botanicheskaya': 'Ботаническая',
}

STATIONS_KEYBOARD = [
    [InlineKeyboardButton('Космонавтов', callback_data='kosmonavtov')],
    [InlineKeyboardButton('Уралмаш', callback_data='uralmash')],
    [InlineKeyboardButton('Машиностроителей', callback_data='mashinostroitelej')],
    [InlineKeyboardButton('Уральская', callback_data='uralskaya')],
    [InlineKeyboardButton('Динамо', callback_data='dinamo')],
    [InlineKeyboardButton('Площадь 1905г', callback_data='ploshad_1905')],
    [InlineKeyboardButton('Геологическая', callback_data='geologicheskaya')],
    [InlineKeyboardButton('Чкаловская', callback_data='chkalovskaya')],
    [InlineKeyboardButton('Ботаническая', callback_data='botanicheskaya')],
]
STATIONS_REPLY_MARKUP = InlineKeyboardMarkup(STATIONS_KEYBOARD)

TO_BOTANICHESKAYA = InlineKeyboardButton(
    'На Ботаническую',
    callback_data='botanicheskaya'
)
TO_KOSMONAVTOV = InlineKeyboardButton(
    'На Космонавтов',
    callback_data='kosmonavtov'
)
END_STATIONS_KEYBOARD = {
    'kosmonavtov': TO_BOTANICHESKAYA,
    'botanicheskaya': TO_KOSMONAVTOV,
}

HELP_TEXT = (
    'Бот показывает время до ближайшего поезда в метро Екатеринбурга.\n'
    'Выбери нужную станцию из списка командой /stations, а затем направление.'
)
