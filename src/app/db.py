import sqlite3
from typing import Optional

import aiosqlite
from telegram import User

from .config import DB_FILENAME, LIMIT_ROW
from .schedule import Schedule
from .utils import is_weekend

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
      AND time_to_train < time('01:00')
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
GET_STATIONS_QUERY = '''
    SELECT
      id_station, name_station
    FROM
     station
    ORDER BY
     id_station;
'''


def schedule_rowfactory(_, row):
    """
    row_factory, который будет возвращать записи из БД в виде экземпляров
     дата-класса Schedule
    """
    return Schedule(*row)


async def select_schedule(from_station: str,
                          to_station: str) -> list[Schedule, ...]:
    """Функция делает запрос к БД с переданными аргументами.
    Возвращает список с объектами Schedule."""
    parameters = (from_station, to_station, await is_weekend(), LIMIT_ROW)
    async with aiosqlite.connect(DB_FILENAME) as db:
        db.row_factory = schedule_rowfactory
        async with db.execute(TIME_TO_TRAIN_QUERY, parameters) as cursor:
            return await cursor.fetchall()


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


def get_stations_from_db() -> list[tuple, ...]:
    """
    Функция делает запрос к БД и возвращает список кортежей с id и именем
     станций.
    """
    with sqlite3.connect(DB_FILENAME) as db:
        cursor = db.execute(GET_STATIONS_QUERY)
        return cursor.fetchall()
