import datetime as dt
from collections import namedtuple

import aiosqlite

from config import DB_FILENAME, SQL_QUERY


class Schedule(namedtuple('Train', ['from_station',
                                    'to_station',
                                    'time_to_train'])):
    """Кастомный namedtuple для удобной обработки записей из БД."""
    __slots__ = ()

    @property
    def direction(self):
        return f'{self.from_station} ➡ {self.to_station}'


def namedtuple_factory(cursor, row):
    """
    row_factory, который будет возвращать записи из БД в виде заданного
    именованного кортежа.
    """
    return Schedule(*row)


async def get_schedule(from_station: str,
                       to_station: str) -> list[Schedule, ...]:
    """Функция делает запрос к БД с переданными аргументами.
    Возвращает список с объектами именованного кортежа."""
    is_weekend = dt.datetime.today().weekday() > 4
    parameters = (from_station, to_station, is_weekend)
    async with aiosqlite.connect(DB_FILENAME) as db:
        db.row_factory = namedtuple_factory
        async with db.execute(SQL_QUERY, parameters) as cursor:
            return await cursor.fetchall()
