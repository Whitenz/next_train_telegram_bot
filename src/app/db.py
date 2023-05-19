import datetime
import os
from typing import Any, Sequence

from sqlalchemy import Row, RowMapping, asc, create_engine, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from telegram import User

from .config import LIMIT_ROW
from .models import BotUser, Favorite, Schedule, Station
from .utils import is_weekend

sync_engine = create_engine(f'postgresql://{os.getenv("PG_DSN")}', echo=True)
sync_session = sessionmaker(bind=sync_engine, expire_on_commit=False)
async_engine = create_async_engine(f'postgresql+asyncpg://{os.getenv("PG_DSN")}',
                                   echo=True)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


def get_stations_from_db() -> Sequence[Row | RowMapping | Any]:
    """Функция делает запрос к БД и возвращает список с объектами Station."""
    with sync_session() as session:
        statement = select(Station)
        return session.scalars(statement).all()


# Словарь со всеми станциями в БД
# Значения не меняются, поэтому подгружается 1 раз из БД при старте приложения
STATIONS_DICT: dict[int, str] = {
    Station.station_id: Station.station_name for Station in get_stations_from_db()
}


async def insert_user_to_db(bot_user: User) -> None:
    """
    Функция делает запрос к БД и добавляет нового пользователя бота в БД>.
    """
    async with async_session() as session:
        statement = insert(
            BotUser
        ).values(
            bot_user_id=bot_user.id,
            first_name=bot_user.first_name,
            last_name=bot_user.last_name,
            username=bot_user.username,
            is_bot=bot_user.is_bot
        ).on_conflict_do_nothing()

        await session.execute(statement)
        await session.commit()


async def select_schedule_from_db(from_station_id: int,
                                  to_station_id: int) -> Sequence[Schedule] | None:
    """
    Функция делает запрос к БД с заданным id станций.
    Возвращает список с объектами Schedule.
    """
    async with async_session() as session:
        statement = select(
            Schedule
        ).where(
            Schedule.from_station_id == from_station_id,
            Schedule.to_station_id == to_station_id,
            Schedule.is_weekend.is_(await is_weekend()),
            Schedule.time_to_train < datetime.timedelta(hours=1)
        ).order_by(
            asc(Schedule.time_to_train)
        ).limit(
            LIMIT_ROW
        )

        return (await session.scalars(statement)).all()


async def insert_favorite_to_db(bot_user_id: int,
                                from_station_id: int,
                                to_station_id: int) -> Favorite | None:
    """
    Функция делает запрос к БД и добавляет избранный маршрут пользователя
    в таблицу 'favorite'. Возвращает созданный объект Favorite.
    """
    async with async_session() as session:
        statement = insert(
            Favorite
        ).values(
            bot_user_id=bot_user_id,
            from_station_id=from_station_id,
            to_station_id=to_station_id
        ).on_conflict_do_nothing(
            constraint='favorite_unique'
        ).returning(
            Favorite
        )

        new_favorite = await session.scalar(statement)
        await session.commit()
        if new_favorite:
            await session.refresh(new_favorite)
        return new_favorite


async def select_favorites_from_db(bot_user_id: int) -> Sequence[Favorite] | None:
    """
    Функция делает запрос к БД и получает из таблицы 'favorite' избранные
    маршруты пользователя. Возвращает список объектов Favorite.
    """
    async with async_session() as session:
        statement = select(
            Favorite
        ).where(
            Favorite.bot_user_id == bot_user_id
        ).order_by(
            Favorite.favorite_id
        )

        return (await session.scalars(statement)).all()


async def delete_favorites_in_db(bot_user_id: int) -> None:
    """
    Функция делает запрос к БД и удаляет из таблицы 'favorite' все избранные
    маршруты пользователя.
    """
    async with async_session() as session:
        statement = delete(
            Favorite
        ).where(
            Favorite.bot_user_id == bot_user_id
        )

        await session.execute(statement)
        await session.commit()


async def favorites_limited(bot_user_id: int) -> bool:
    """
    Функция делает запрос к БД и проверяет количество избранных маршрутов в
     таблице 'favorite' для данного пользователя. Возвращает результат
      сравнения с максимальным допустимым количеством избранного.
    """
    async with async_session() as session:
        statement = select(
            func.count()
        ).select_from(
            Favorite
        ).where(
            Favorite.bot_user_id == bot_user_id
        )

        count = await session.scalar(statement)
        return count >= LIMIT_ROW
