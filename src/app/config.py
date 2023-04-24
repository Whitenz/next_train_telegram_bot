import datetime as dt
import logging
import os

from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_FILENAME = os.path.join(BASE_DIR, 'data', 'schedule.sqlite3')
LIMIT_ROW = 2  # берем из БД для бота только два ближайших поезда

# Параметры для ConversationHandler's
CHOICE_DIRECTION, FINAL_STAGE = range(2)
CONVERSATION_TIMEOUT = 60 * 3  # время ожидания ответа от пользователя (сек)

# Часы работы метрополитена. Интервал расширен на 0.5 часа в обе стороны
# для отображения всех поездов до/после открытия/закрытия
OPEN_TIME_METRO = dt.time(hour=5, minute=30)
CLOSE_TIME_METRO = dt.time(hour=0, minute=30)

# Конфигурация логгера
LOG_FILENAME = os.path.join(BASE_DIR, 'data', 'bot.log')
LOGGER_TEXT = 'Пользователь {first_name} ({id_bot_user}) отправил команду "{command}"'
logging.basicConfig(
    filename=LOG_FILENAME,
    format='[%(asctime)s] - [%(name)s] - [%(levelname)s] => %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S',
    level=logging.INFO,
    encoding='utf-8'
)
