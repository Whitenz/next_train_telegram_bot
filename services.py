import datetime as dt
import sqlite3
from collections import namedtuple

from config import DB_FILENAME, SQL_QUERY


class Schedule(namedtuple('Train', ['from_station',
                                    'to_station',
                                    'time_to_train'])):
    """Кастомный namedtuple для удобной обработки записей из БД."""
    __slots__ = ()

    @property
    def direction(self):
        # &#8594 - HTML код (правая стрелка)
        return f'{self.from_station} &#8594 {self.to_station}'


def namedtuple_factory(cursor, row):
    """
    row_factory, который будет возвращать записи из БД в виде заданного
    именованного кортежа.
    """
    return Schedule(*row)


# Подключаемся к БД
CONN = sqlite3.connect(DB_FILENAME)
CONN.row_factory = namedtuple_factory


def get_schedule(from_station: str, to_station: str) -> list[Schedule, ...]:
    """Функция делает запрос к БД с переданными аргументами.
    Возвращает список с объектами именованного кортежа."""
    is_weekend = dt.datetime.today().weekday() > 4
    cursor = CONN.cursor()
    cursor.execute(SQL_QUERY, (from_station, to_station, is_weekend))
    return cursor.fetchall()
