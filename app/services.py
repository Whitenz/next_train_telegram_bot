import datetime as dt
from dataclasses import dataclass

import aiosqlite

from config import (CLOSE_TIME_METRO, DB_FILENAME, LIMIT_ROW,
                    OPEN_TIME_METRO, TIME_TO_TRAIN_QUERY)


@dataclass
class Schedule:
    from_station: str
    to_station: str
    time_to_train: str

    def __post_init__(self):
        datetime_obj = dt.datetime.strptime(self.time_to_train, '%H:%M:%S')
        self.time_to_train = datetime_obj.strftime('%M:%S')

    @property
    def direction(self):
        return f'{self.from_station} ➡ {self.to_station}'


def custom_rowfactory(cursor, row):
    """
    row_factory, который будет возвращать записи из БД в виде экземпляров
     дата-класса Scheduleю
    """
    return Schedule(*row)


def is_weekend() -> bool:
    """Функция проверяет выходной сейчас день или нет."""
    today = dt.datetime.now()
    delta = dt.timedelta(minutes=30)
    return (today - delta).isoweekday() > 5


def metro_is_closed() -> bool:
    """Функция проверяет закрыто ли метро в соответствии с часами работы."""
    return CLOSE_TIME_METRO <= dt.datetime.now().time() <= OPEN_TIME_METRO


async def get_schedule(from_station: str,
                       to_station: str) -> list[Schedule, ...]:
    """Функция делает запрос к БД с переданными аргументами.
    Возвращает список с объектами именованного кортежа."""
    parameters = (from_station, to_station, is_weekend(), LIMIT_ROW)
    async with aiosqlite.connect(DB_FILENAME) as db:
        db.row_factory = custom_rowfactory
        async with db.execute(TIME_TO_TRAIN_QUERY, parameters) as cursor:
            return await cursor.fetchall()


def get_text_with_time_to_train(schedule):
    if len(schedule) >= 2:
        return (
            f'<b>{schedule[0].direction}:</b>\n\n'
            f'ближайший поезд через {schedule[0].time_to_train} (мин:с)\n'
            f'следующий через {schedule[1].time_to_train} (мин:с)'
        )
    elif len(schedule) == 1:
        return (
            f'<b>{schedule[0].direction}:</b>\n\n'
            f'последний поезд через {schedule[0].time_to_train} (мин:с)'
        )
    return f'По расписанию поездов сегодня больше нет.'
