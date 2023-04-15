import datetime as dt
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Получаем токен бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Параметры и запросы для работы с SQL БД
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_FILENAME = os.path.join(BASE_DIR, 'data', 'schedule.sqlite3')
LIMIT_ROW = 2  # берем из БД для бота только два ближайших поезда
TIME_TO_TRAIN_QUERY = '''
    SELECT
      st1.name_station AS from_station,
      st2.name_station AS to_station,
      time(
          strftime('%s', sc.departure_time) - strftime('%s', 'now', 'localtime'),
          'unixepoch'
      ) AS time_to_train
    FROM
      schedule AS sc
      INNER JOIN station AS st1 ON st1.id_station = sc.from_station
      INNER JOIN station AS st2 ON st2.id_station = sc.to_station
    WHERE
      st1.name_station = ?
      AND st2.name_station = ?
      AND sc.is_weekend IS ?
      AND time_to_train < time('00:25')
    ORDER BY
      time_to_train
    LIMIT
      ?;
'''
ADD_FAVORITE_QUERY = '''
    INSERT OR IGNORE INTO
      favorite (id_bot_user, from_station, to_station)
    VALUES (
      ?,
      (SELECT id_station FROM station WHERE name_station = ?),
      (SELECT id_station FROM station WHERE name_station = ?)
    );
'''
GET_FAVORITES_QUERY = '''
    SELECT
      st1.name_station AS from_station,
      st2.name_station AS to_station
    FROM
      favorite AS f
      INNER JOIN station AS st1 on st1.id_station = f.from_station
      INNER JOIN station AS st2 on st2.id_station = f.to_station
    WHERE
      id_bot_user = ?;
'''
CLEAR_FAVORITES_QUERY = '''
    DELETE
    FROM
      favorite
    WHERE
      id_bot_user = ?;
'''
CHECK_LIMIT_FAVORITES_QUERY = '''
    SELECT
      COUNT(*) >= ? AS result
    FROM
      favorite
    WHERE
      id_bot_user = ?;
'''
ADD_USER_QUERY = '''
    INSERT OR IGNORE INTO
      user (id_bot_user, first_name, last_name, username, is_bot)
    VALUES (
        ?, ?, ?, ?, ?
    );
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

# Клавиатура для Telegram бота для выбора направления движения поезда
DIRECTION_KEYBOARD = [
    [
        InlineKeyboardButton('На Ботаническую', callback_data='Ботаническая'),
        InlineKeyboardButton('На Космонавтов', callback_data='Космонавтов'),
    ]
]
DIRECTION_REPLY_MARKUP = InlineKeyboardMarkup(DIRECTION_KEYBOARD)

# Словарь для выбора направления на конечных станциях, где 'from_station' ключ,
# а 'to_station' значение (добавлен, т.к. нет смысла выбирать пользователю)
END_STATION_DIRECTION = {
    'Космонавтов': 'Ботаническая',
    'Ботаническая': 'Космонавтов',
}

# Состояния для ConversationHandler's
CHOICE_DIRECTION, GET_TIME_TO_TRAIN = range(2)
NEW_FAVORITE = 1

# Часы работы метрополитена. Интервал расширен на 0.5 часа в обе стороны
# для отображения всех поездов до/после открытия/закрытия
OPEN_TIME_METRO = dt.time(hour=5, minute=30)
CLOSE_TIME_METRO = dt.time(hour=0, minute=30)
