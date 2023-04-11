import datetime as dt
from dataclasses import dataclass
from typing import Optional

import aiosqlite
from telegram import User

from app.config import (ADD_FAVORITE_QUERY, ADD_USER_QUERY,
                        CHECK_LIMIT_FAVORITES_QUERY, CLEAR_FAVORITES_QUERY,
                        CLOSE_TIME_METRO, DB_FILENAME, GET_FAVORITES_QUERY,
                        LIMIT_ROW, OPEN_TIME_METRO, TIME_TO_TRAIN_QUERY)
from app.messages import (TEXT_WITH_TIME_NONE, TEXT_WITH_TIME_ONE_TRAIN,
                          TEXT_WITH_TIME_TWO_TRAINS)


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


def schedule_rowfactory(_, row):
    """
    row_factory, который будет возвращать записи из БД в виде экземпляров
     дата-класса Schedule
    """
    return Schedule(*row)


async def is_weekend() -> bool:
    """Функция проверяет выходной сейчас день или нет."""
    today = dt.datetime.now()
    delta = dt.timedelta(minutes=30)
    return (today - delta).isoweekday() > 5


async def metro_is_closed() -> bool:
    """Функция проверяет закрыто ли метро в соответствии с часами работы."""
    return CLOSE_TIME_METRO <= dt.datetime.now().time() <= OPEN_TIME_METRO


async def select_schedule(from_station: str,
                          to_station: str) -> list[Schedule, ...]:
    """Функция делает запрос к БД с переданными аргументами.
    Возвращает список с объектами Schedule."""
    parameters = (from_station, to_station, await is_weekend(), LIMIT_ROW)
    async with aiosqlite.connect(DB_FILENAME) as db:
        db.row_factory = schedule_rowfactory
        async with db.execute(TIME_TO_TRAIN_QUERY, parameters) as cursor:
            return await cursor.fetchall()


async def format_text_with_time_to_train(schedule):
    if len(schedule) >= 2:
        return TEXT_WITH_TIME_TWO_TRAINS.format(
            direction=schedule[0].direction,
            time_to_train_1=schedule[0].time_to_train,
            time_to_train_2=schedule[1].time_to_train,

        )
    if len(schedule) == 1:
        return TEXT_WITH_TIME_ONE_TRAIN.format(
            direction=schedule[0].direction,
            time_to_train_1=schedule[0].time_to_train
        )
    return TEXT_WITH_TIME_NONE


async def insert_favorite_to_db(id_bot_user: int,
                                from_station: str,
                                to_station: str) -> None:
    """
    Функция делает запрос к БД и добавляет избранный маршрут пользователя
    в таблицу 'favorite'.
    """

    async with aiosqlite.connect(DB_FILENAME) as db:
        await db.execute(ADD_FAVORITE_QUERY,
                         (id_bot_user, from_station, to_station))
        await db.commit()


async def select_favorites_from_db(id_bot_user) -> list[tuple]:
    """
    Функция делает запрос к БД и получает из таблицы 'favorite' избранные
    маршруты пользователя. Возвращает их в виде списка кортежей вида
    (from_station, to_station)
    """
    async with aiosqlite.connect(DB_FILENAME) as db:
        async with db.execute(GET_FAVORITES_QUERY, (id_bot_user,)) as cursor:
            return await cursor.fetchall()


async def delete_favorites_in_db(id_bot_user) -> None:
    """
    Функция делает запрос к БД и удаляет из таблицы 'favorite' все избранные
    маршруты пользователя.
    """
    async with aiosqlite.connect(DB_FILENAME) as db:
        await db.execute(CLEAR_FAVORITES_QUERY, (id_bot_user,))
        await db.commit()


async def favorites_limited(id_bot_user) -> list:
    """
    Функция делает запрос к БД и проверяет количество избранных маршрутов в
     таблице 'favorite' для данного пользователя..
    """
    async with aiosqlite.connect(DB_FILENAME) as db:
        async with db.execute(CHECK_LIMIT_FAVORITES_QUERY,
                              (LIMIT_ROW, id_bot_user)) as cursor:
            result = await cursor.fetchone()
            return result[0]


async def insert_user_to_db(bot_user: Optional[User]) -> None:
    """
    Функция делает запрос к БД и добавляет нового пользователя бота в таблицу
     'user'.
    """
    async with aiosqlite.connect(DB_FILENAME) as db:
        parameters = (bot_user.id, bot_user.first_name, bot_user.last_name,
                      bot_user.username, bot_user.is_bot)
        await db.execute(ADD_USER_QUERY, parameters)
        await db.commit()
