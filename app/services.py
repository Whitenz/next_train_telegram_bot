import datetime as dt
from collections import namedtuple

from config import DB_FILENAME, LIMIT_ROW, SQL_QUERY, MAX_AWAIT_TRAIN

import aiosqlite


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


def is_weekend() -> bool:
    today = dt.datetime.today()
    delta = dt.timedelta(minutes=30)
    return (today - delta).isoweekday() > 5


async def get_schedule(from_station: str,
                       to_station: str) -> list[Schedule, ...]:
    """Функция делает запрос к БД с переданными аргументами.
    Возвращает список с объектами именованного кортежа."""
    parameters = (from_station, to_station, is_weekend(),
                  MAX_AWAIT_TRAIN, LIMIT_ROW)
    async with aiosqlite.connect(DB_FILENAME) as db:
        db.row_factory = namedtuple_factory
        async with db.execute(SQL_QUERY, parameters) as cursor:
            return await cursor.fetchall()


def get_text_with_time_to_train(schedule):
    if len(schedule) == 2:
        return (
            f'<b>{schedule[0].direction}:</b>\n\n'
            f'ближайший поезд через {schedule[0].time_to_train} (ч:мин:с)\n'
            f'следующий через {schedule[1].time_to_train} (ч:мин:с)'
        )
    elif len(schedule) == 1:
        return (
            f'<b>{schedule[0].direction}:</b>\n\n'
            f'последний поезд через {schedule[0].time_to_train} (ч:мин:с)'
        )
    return f'По расписанию поездов сегодня больше нет.'
