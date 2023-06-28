import datetime
from typing import Sequence

from sqlalchemy import URL, Engine, asc, create_engine, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import Session, sessionmaker

from telegram import User

from app import utils
from app.config import settings
from app.models import BotUser, Favorite, Schedule, Station

URL_DB_SYNC: URL = URL.create(
    drivername=settings.DB_DRIVERNAME_SYNC,
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME
)
URL_DB_ASYNC: URL = URL_DB_SYNC.set(drivername=settings.DB_DRIVERNAME_ASYNC)
sync_engine: Engine = create_engine(url=URL_DB_SYNC, echo=True)
sync_session: sessionmaker[Session] = sessionmaker(
    bind=sync_engine, expire_on_commit=False
)
async_engine: AsyncEngine = create_async_engine(url=URL_DB_ASYNC, echo=True)
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine, expire_on_commit=False
)


def get_stations(
        current_session: sessionmaker[Session] = sync_session
) -> Sequence[Station]:
    """Извлекает данные из таблицы 'station'.

    Args:
        current_session: Фабрика для синхронной сессии.

    Returns:
        Коллекция объектов Station.
    """
    with current_session() as session:
        statement = select(Station)
        return session.scalars(statement).all()


async def insert_user(
        bot_user: User,
        current_session: async_sessionmaker[AsyncSession] = async_session,
) -> None:
    """Добавляет нового пользователя бота в таблицу 'user'.

    Args:
        bot_user: Пользователь бота.
        current_session: Фабрика для синхронной сессии.

    Returns:
        None
    """
    async with current_session() as session:
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


async def select_schedule(
        from_station_id: int,
        to_station_id: int,
        current_session: async_sessionmaker[AsyncSession] = async_session,
) -> Sequence[Schedule | None]:
    """Извлекает данные из таблицы 'schedule'.

    Функция делает запрос к БД с переданными id станций и возвращает список с объектами
    Schedule при наличии подходящих под временной интервал.

    Args:
        from_station_id: id станции отправления поезда.
        to_station_id: id конечной станции направления движения поездов.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        Коллекция объектов Schedule соответствующих запросу из БД или None.
    """
    async with current_session() as session:
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


async def insert_favorite(
        bot_user: User,
        from_station_id: int,
        to_station_id: int,
        current_session: async_sessionmaker[AsyncSession] = async_session
) -> Favorite | None:
    """Добавляет избранный маршрут в таблицу 'favorite'.

    Функция делает запрос к БД и добавляет избранный маршрут пользователя в таблицу
    'favorite'. При уникальности маршрута возвращает новую запись в виде объектов
    Favorite. Иначе возвращает None.

    Args:
        bot_user: Пользователь бота.
        from_station_id: id станции отправления поезда.
        to_station_id: id конечной станции направления движения поездов.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        Объект Favorite, если добавлена новая запись в БД. Иначе возвращает None.
    """
    async with current_session() as session:
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


async def select_favorites(
        bot_user: User,
        current_session: async_sessionmaker[AsyncSession] = async_session
) -> Sequence[Favorite | None]:
    """Извлекает избранный маршрут пользователя из таблицы 'favorite'.

    Функция делает запрос к БД с переданным id пользователя бота для извлечения
    его избранных маршрутов. Возвращает их при наличии в виде коллекции объектов
    Favorite. Иначе возвращает None.

    Args:
        bot_user: Пользователь бота.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        Коллекция объектов Favorite соответствующих запросу из БД или None.
    """
    async with current_session() as session:
        statement = select(
            Favorite
        ).where(
            Favorite.bot_user_id == bot_user.id
        ).order_by(
            Favorite.favorite_id
        )

        return (await session.scalars(statement)).all()


async def delete_favorites(
        bot_user: User,
        current_session: async_sessionmaker[AsyncSession] = async_session
) -> None:
    """Удаляет избранный маршрут пользователя из таблицы 'favorite'.

    Функция делает запрос к БД с id пользователя и удаляет из таблицы 'favorite' все его
    избранные маршруты.

    Args:
        bot_user: Пользователь бота.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        None
    """
    async with current_session() as session:
        statement = delete(
            Favorite
        ).where(
            Favorite.bot_user_id == bot_user.id
        )

        await session.execute(statement)
        await session.commit()


async def favorites_limited(
        bot_user: User,
        current_session: async_sessionmaker[AsyncSession] = async_session) -> bool:
    """Проверяет лимит избранных маршрутов пользователя в таблице 'favorite'.

    Функция делает запрос к БД и проверяет количество избранных маршрутов в таблице
    'favorite' для данного пользователя. Возвращает результат проверки достигнут лимит
    максимального количества избранных маршрутов на одного пользователя, указанного в
    конфигурации.

    Args:
        bot_user: Пользователь бота.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        True, если достигнут лимит на избранное, иначе False.
    """
    async with current_session() as session:
        statement = select(
            func.count()
        ).select_from(
            Favorite
        ).where(
            Favorite.bot_user_id == bot_user.id
        )

        count = await session.scalar(statement)
        return count >= settings.LIMIT_FAVORITES
