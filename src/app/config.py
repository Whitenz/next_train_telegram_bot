import datetime as dt
import os

from dotenv import load_dotenv

# Получаем токен бота
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Параметры для работы с SQL БД
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_FILENAME = os.path.join(BASE_DIR, 'data', 'schedule.sqlite3')
LIMIT_ROW = 2  # берем из БД для бота только два ближайших поезда

# Параметры для ConversationHandler's
CHOICE_DIRECTION, GET_TIME_TO_TRAIN = range(2)
NEW_FAVORITE = 1
CONVERSATION_TIMEOUT = 60 * 3  # время ожидания ответа от пользователя (сек)

# Часы работы метрополитена. Интервал расширен на 0.5 часа в обе стороны
# для отображения всех поездов до/после открытия/закрытия
OPEN_TIME_METRO = dt.time(hour=5, minute=30)
CLOSE_TIME_METRO = dt.time(hour=0, minute=30)
