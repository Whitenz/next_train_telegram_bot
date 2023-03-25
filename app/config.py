import os
import datetime as dt

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Получаем токен бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Параметры для работы с SQL БД
DB_NAME = 'schedule'
DB_FILENAME = DB_NAME + '.sqlite3'
MAX_AWAIT_TRAIN = '01:00'
LIMIT_ROW = 2
# Запрос получает из базы расчетное время до ближайших поездов
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
      AND  time_to_train < time(?)
    LIMIT 
      ?;
'''

# Клавиатура для Telegram бота для выбора станции отправления
STATIONS_KEYBOARD = [
    [InlineKeyboardButton('Космонавтов', callback_data='Космонавтов')],
    [InlineKeyboardButton('Уралмаш', callback_data='Уралмаш')],
    [InlineKeyboardButton('Машиностроителей',
                          callback_data='Машиностроителей')],
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

# Состояния для ConversationHandler
CHOICE_DIRECTION, GET_TIME_TO_TRAIN = range(2)

# Часы работы метрополитена. Интервал расширен на 0.5 часа в обе стороны
# для отображения всех поездов до/после открытия/закрытия
OPEN_TIME_METRO = dt.time(hour=5, minute=30)
CLOSE_TIME_METRO = dt.time(hour=0, minute=30)
METRO_IS_CLOSED_TEXT = ('Метрополитен закрыт. Часы работы с 06:00 до 00:00. '
                        'Расписание будет доступно с 05:30.')
