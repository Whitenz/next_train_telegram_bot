import datetime as dt
import sqlite3

from config import DB_FILENAME, SQL_QUERY

# Connect to the SQLite database
CONN = sqlite3.connect(DB_FILENAME)


def get_schedule(from_station: str, to_station: str) -> list[tuple]:
    """Функция делает запрос к БД с переданными аргументами.
    Возвращает список с двумя записями из БД - время до ближайших поездов."""
    is_weekend = dt.datetime.today().weekday() > 4
    cursor = CONN.cursor()
    cursor.execute(SQL_QUERY, (from_station, to_station, is_weekend))
    return cursor.fetchall()
