import datetime

from sqlalchemy import (CheckConstraint, ForeignKey, func, String, UniqueConstraint)
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column, MappedAsDataclass,
                            relationship)
from typing_extensions import Annotated

TIMESTAMP_TYPE = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.now())
]
STATION_FK = Annotated[
    int,
    mapped_column(
        ForeignKey('station.station_id', onupdate='CASCADE', ondelete='CASCADE'))
]


class Base(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""
    pass


class Station(Base):
    __tablename__ = 'station'

    station_id: Mapped[int] = mapped_column(primary_key=True)
    station_name: Mapped[str] = mapped_column(String(30), unique=True)


class Schedule(Base):
    __tablename__ = 'schedule'

    schedule_id: Mapped[int] = mapped_column(primary_key=True)
    from_station_id: Mapped[STATION_FK] = mapped_column(
        ForeignKey('station.station_id', onupdate='CASCADE', ondelete='CASCADE'))
    to_station_id: Mapped[STATION_FK] = mapped_column(
        ForeignKey('station.station_id', onupdate='CASCADE', ondelete='CASCADE'))
    is_weekend: Mapped[bool]
    departure_time: Mapped[datetime.time]

    from_station_obj: Mapped['Station'] = relationship(foreign_keys=from_station_id)
    to_station_obj: Mapped['Station'] = relationship(foreign_keys=to_station_id)

    __table_args__ = (
        CheckConstraint('from_station_id != to_station_id', name='route_check'),
        UniqueConstraint('from_station_id', 'to_station_id', 'is_weekend',
                         'departure_time', name='schedule_unique')
    )


class User(Base):
    __tablename__ = 'user'

    bot_user_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str | None] = mapped_column(unique=True)
    is_bot: Mapped[bool]
    created_at: Mapped[TIMESTAMP_TYPE]


class Favorite(Base):
    __tablename__ = 'favorite'

    favorite_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bot_user_id: Mapped[int] = mapped_column(ForeignKey('user.bot_user_id'))
    from_station_id: Mapped[STATION_FK] = mapped_column(
        ForeignKey('station.station_id', onupdate='CASCADE', ondelete='CASCADE'))
    to_station_id: Mapped[STATION_FK] = mapped_column(
        ForeignKey('station.station_id', onupdate='CASCADE', ondelete='CASCADE'))

    from_station_obj: Mapped['Station'] = relationship(foreign_keys=from_station_id)
    to_station_obj: Mapped['Station'] = relationship(foreign_keys=to_station_id)

    __table_args__ = (
        UniqueConstraint('bot_user_id', 'from_station_id', 'to_station_id',
                         name='favorite_unique'),
    )
