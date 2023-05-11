import datetime
import os
from typing import Any, Sequence

from sqlalchemy import Row, RowMapping, asc, create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from .models import Schedule, Station
from .utils import is_weekend

sync_engine = create_engine(f'postgresql://{os.getenv("PG_DB")}')
sync_session = sessionmaker(bind=sync_engine, expire_on_commit=False)
async_engine = create_async_engine(f'postgresql+asyncpg://{os.getenv("PG_DB")}')
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


def get_stations_from_db() -> Sequence[Row | RowMapping | Any]:
    """Функция делает запрос к БД и возвращает список с объектами Station."""
    with sync_session() as session:
        stations = session.scalars(select(Station)).all()
        return stations


async def select_schedule_orm(from_station: str,
                              to_station: str) -> Sequence[Row | RowMapping | Any]:
    """Функция делает запрос к БД с переданными аргументами.
    Возвращает список с объектами Schedule."""
    from_station_id = STATIONS_DICT.get(from_station)
    to_station_id = STATIONS_DICT.get(to_station)

    async with async_session() as session:
        stmt = select(
            Schedule
        ).where(
            Schedule.from_station_id == from_station_id,
            Schedule.to_station_id == to_station_id,
            Schedule.is_weekend.is_(await is_weekend()),
            Schedule.time_to_train < datetime.timedelta(hours=1)
        ).order_by(
            asc(Schedule.time_to_train)
        ).limit(
            2
        )

        schedules = (await session.scalars(stmt)).all()
        return schedules


# Словарь со всеми станциями в БД
STATIONS_DICT = {
    Station.station_name: Station.station_id for Station in get_stations_from_db()
}
