import os
import datetime as dt

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Получаем токен бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Параметры для работы с SQL БД
DB_FILENAME = 'schedule.sqlite3'
LIMIT_ROW = 2  # берем из БД для бота только два ближайших поезда

TIME_TO_TRAIN_QUERY = f'''
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
    ORDER BY
      time_to_train
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
# Текст для команды /help
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
