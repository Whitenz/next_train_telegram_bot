import datetime
import typing as t

from sqlalchemy import (
    URL,
    CursorResult,
    Engine,
    asc,
    create_engine,
    delete,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from telegram import User

from . import utils
from .config import settings
from .models import (
    BotUser,
    Favorite,
    Schedule,
    Station,
)

URL_DB_SYNC: URL = URL.create(
    drivername=settings.DB_DRIVERNAME_SYNC,
    username=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)
URL_DB_ASYNC: URL = URL_DB_SYNC.set(drivername=settings.DB_DRIVERNAME_ASYNC)
sync_engine: Engine = create_engine(url=URL_DB_SYNC, echo=True)
sync_session: sessionmaker[Session] = sessionmaker(bind=sync_engine, expire_on_commit=False)
async_engine: AsyncEngine = create_async_engine(url=URL_DB_ASYNC, echo=True)
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(async_engine, expire_on_commit=False)


def get_stations(current_session: sessionmaker[Session] = sync_session) -> t.Sequence[Station]:
    """Извлекает данные из таблицы 'station'.

    Args:
        current_session: Фабрика для синхронной сессии.

    Returns:
        Коллекция объектов Station.
    """
    statement = select(Station)

    with current_session() as session:
        return session.scalars(statement).all()


async def insert_user(
    telegram_user: User,
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> None:
    """Добавляет нового пользователя бота в таблицу 'bot_user'.

    Args:
        telegram_user: Пользователь бота.
        current_session: Фабрика для синхронной сессии.

    Returns:
        None
    """
    statement = (
        insert(BotUser)
        .values(
            bot_user_id=telegram_user.id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
            is_bot=telegram_user.is_bot,
        )
        .on_conflict_do_nothing()
    )

    async with current_session() as session:
        await session.execute(statement)
        await session.commit()


async def select_schedule(
    from_station_id: int,
    to_station_id: int,
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> t.Sequence[Schedule]:
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
    statement = (
        select(Schedule)
        .where(
            Schedule.from_station_id == from_station_id,
            Schedule.to_station_id == to_station_id,
            Schedule.is_weekend.is_(await utils.is_weekend()),
            Schedule.time_to_train < datetime.timedelta(minutes=settings.MAX_WAITING_TIME),
        )
        .order_by(asc(Schedule.time_to_train))
        .limit(settings.LIMIT_ROW)
    )

    async with current_session() as session:
        return (await session.scalars(statement)).all()


async def insert_favorite(
    telegram_user: User,
    from_station_id: int,
    to_station_id: int,
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> Favorite | None:
    """Добавляет избранный маршрут в таблицу 'favorite'.

    Функция делает запрос к БД и добавляет избранный маршрут пользователя в таблицу
    'favorite'. При уникальности маршрута возвращает новую запись в виде объектов
    Favorite. Иначе возвращает None.

    Args:
        telegram_user: Пользователь бота.
        from_station_id: id станции отправления поезда.
        to_station_id: id конечной станции направления движения поездов.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        Объект Favorite, если добавлена новая запись в БД. Иначе возвращает None.
    """
    statement = (
        insert(Favorite)
        .values(
            bot_user_id=telegram_user.id,
            from_station_id=from_station_id,
            to_station_id=to_station_id,
        )
        .on_conflict_do_nothing(constraint="favorite_unique")
        .returning(Favorite)
    )

    async with current_session() as session:
        new_favorite = await session.scalar(statement)
        await session.commit()
        if new_favorite:
            await session.refresh(new_favorite)
        return new_favorite


async def select_favorites(
    telegram_user: User,
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> t.Sequence[Favorite]:
    """Извлекает избранный маршрут пользователя из таблицы 'favorite'.

    Функция делает запрос к БД с переданным id пользователя бота для извлечения
    его избранных маршрутов. Возвращает их при наличии в виде коллекции объектов
    Favorite. Иначе возвращает None.

    Args:
        telegram_user: Пользователь бота.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        Коллекция объектов Favorite соответствующих запросу из БД или None.
    """
    statement = (
        select(Favorite)
        .where(
            Favorite.bot_user_id == telegram_user.id,
        )
        .order_by(Favorite.favorite_id)
    )

    async with current_session() as session:
        return (await session.scalars(statement)).all()


async def delete_favorites(
    telegram_user: User,
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> None:
    """Удаляет избранный маршрут пользователя из таблицы 'favorite'.

    Функция делает запрос к БД с id пользователя и удаляет из таблицы 'favorite' все его
    избранные маршруты.

    Args:
        telegram_user: Пользователь бота.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        None
    """
    statement = delete(Favorite).where(
        Favorite.bot_user_id == telegram_user.id,
    )

    async with current_session() as session:
        await session.execute(statement)
        await session.commit()


async def favorites_limited(
    telegram_user: User,
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> bool:
    """Проверяет лимит избранных маршрутов пользователя в таблице 'favorite'.

    Функция делает запрос к БД и проверяет количество избранных маршрутов в таблице
    'favorite' для данного пользователя. Возвращает результат проверки достигнут лимит
    максимального количества избранных маршрутов на одного пользователя, указанного в
    конфигурации.

    Args:
        telegram_user: Пользователь бота.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        True, если достигнут лимит на избранное, иначе False.
    """
    statement = (
        select(func.count())
        .select_from(Favorite)
        .where(
            Favorite.bot_user_id == telegram_user.id,
        )
    )

    async with current_session() as session:
        count = await session.scalar(statement)
        if not isinstance(count, int):
            raise TypeError
        return count >= settings.LIMIT_FAVORITES


async def select_all_users(
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> list[BotUser]:
    """Select all users from the database.

    Returns:
        List of all BotUser objects.
    """
    statement = select(BotUser)

    async with current_session() as session:
        return list((await session.scalars(statement)).all())


async def delete_user(
    user_id: int,
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> bool:
    """Delete a user from the database.

    Args:
        user_id: Telegram user ID to delete.
        current_session: Async session factory for DB access.

    Returns:
        True if user was deleted, False if not found.
    """
    statement = delete(BotUser).where(BotUser.bot_user_id == user_id)

    async with current_session() as session:
        # Для DML-запросов execute возвращает CursorResult с rowcount
        result = t.cast("CursorResult[t.Any]", await session.execute(statement))
        await session.commit()
        return bool(result.rowcount)


async def delete_users(
    user_ids: t.Sequence[int],
    current_session: async_sessionmaker[AsyncSession] = async_session,
) -> int:
    """Удаляет нескольких пользователей из таблицы 'bot_user' одним запросом.

    Args:
        user_ids: Коллекция Telegram user ID для удаления.
        current_session: Фабрика для асинхронной сессии.

    Returns:
        Количество удалённых пользователей.
    """
    if not user_ids:
        return 0

    statement = delete(BotUser).where(BotUser.bot_user_id.in_(user_ids))

    async with current_session() as session:
        # Для DML-запросов execute возвращает CursorResult с rowcount
        result = t.cast("CursorResult[t.Any]", await session.execute(statement))
        await session.commit()
        return int(result.rowcount or 0)
