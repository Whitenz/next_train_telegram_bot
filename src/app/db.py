import datetime
from typing import Sequence

from sqlalchemy import URL, asc, create_engine, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from telegram import User

from app import utils
from app.config import settings
from app.models import BotUser, Favorite, Schedule, Station

URL_DB_SYNC = URL.create(
    drivername=settings.DB_DRIVERNAME_SYNC,
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME
)
URL_DB_ASYNC = URL_DB_SYNC.set(drivername=settings.DB_DRIVERNAME_ASYNC)
sync_engine = create_engine(url=URL_DB_SYNC, echo=True)
sync_session = sessionmaker(bind=sync_engine, expire_on_commit=False)
async_engine = create_async_engine(url=URL_DB_ASYNC, echo=True)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


def get_stations() -> Sequence[Station]:
    """Функция делает запрос к БД и возвращает список с объектами Station."""
    with sync_session() as session:
        statement = select(Station)
        return session.scalars(statement).all()


# Словарь со всеми станциями в БД
# Значения не меняются, поэтому подгружается 1 раз из БД при старте приложения
STATIONS_DICT: dict[int, str] = {
    Station.station_id: Station.station_name for Station in get_stations()
}


async def insert_user(bot_user: User) -> None:
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


async def select_schedule(from_station_id: int,
                          to_station_id: int) -> Sequence[Schedule | None]:
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
            Schedule.is_weekend.is_(await utils.is_weekend()),
            Schedule.time_to_train < datetime.timedelta(
                minutes=settings.MAX_WAITING_TIME
            )
        ).order_by(
            asc(Schedule.time_to_train)
        ).limit(
            settings.LIMIT_ROW
        )

        return (await session.scalars(statement)).all()


async def insert_favorite(bot_user: User,
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
            bot_user_id=bot_user.id,
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


async def select_favorites(bot_user: User) -> Sequence[Favorite | None]:
    """
    Функция делает запрос к БД и получает из таблицы 'favorite' избранные
    маршруты пользователя. Возвращает список объектов Favorite.
    """
    async with async_session() as session:
        statement = select(
            Favorite
        ).where(
            Favorite.bot_user_id == bot_user.id
        ).order_by(
            Favorite.favorite_id
        )

        return (await session.scalars(statement)).all()


async def delete_favorites(bot_user: User) -> None:
    """
    Функция делает запрос к БД и удаляет из таблицы 'favorite' все избранные
    маршруты пользователя.
    """
    async with async_session() as session:
        statement = delete(
            Favorite
        ).where(
            Favorite.bot_user_id == bot_user.id
        )

        await session.execute(statement)
        await session.commit()


async def favorites_limited(bot_user: User) -> bool:
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
            Favorite.bot_user_id == bot_user.id
        )

        count = await session.scalar(statement)
        return count >= settings.LIMIT_FAVORITES
