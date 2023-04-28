import datetime

from sqlalchemy import (CheckConstraint, ForeignKey, String, UniqueConstraint,
                        create_engine, func)
from sqlalchemy.orm import (DeclarativeBase, Mapped, MappedAsDataclass,
                            mapped_column, sessionmaker)
from typing_extensions import Annotated

from .config import DB_FILENAME


ENGINE = create_engine(f'sqlite:///{DB_FILENAME}', echo=True)
Session = sessionmaker(ENGINE)

TIMESTAMP_TYPE = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.now())
]


class Base(MappedAsDataclass, DeclarativeBase):
    """subclasses will be converted to dataclasses"""
    pass


class Station(Base):
    __tablename__ = 'station'

    id_station: Mapped[int] = mapped_column(primary_key=True)
    name_station: Mapped[str] = mapped_column(String(30), unique=True)


class Schedule(Base):
    __tablename__ = 'schedule'

    id_schedule: Mapped[int] = mapped_column(primary_key=True)
    from_station: Mapped[int] = mapped_column(ForeignKey('station.id_station',
                                                         onupdate='CASCADE',
                                                         ondelete='CASCADE'))
    to_station: Mapped[int] = mapped_column(ForeignKey('station.id_station',
                                                       onupdate='CASCADE',
                                                       ondelete='CASCADE'))
    is_weekend: Mapped[bool]
    departure_time: Mapped[datetime.time]

    __table_args__ = (
        CheckConstraint('from_station != to_station', name='route_check'),
        UniqueConstraint('from_station', 'to_station', 'is_weekend',
                         'departure_time', name='schedule_unique')
    )


class User(Base):
    __tablename__ = 'user'

    id_bot_user: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str | None] = mapped_column(unique=True)
    is_bot: Mapped[bool]
    created_at: Mapped[TIMESTAMP_TYPE]


class Favorite(Base):
    __tablename__ = 'favorite'

    id_favorite: Mapped[int] = mapped_column(primary_key=True)
    id_bot_user: Mapped[int] = mapped_column(ForeignKey('user.id_bot_user'))
    from_station: Mapped[int] = mapped_column(ForeignKey('station.id_station',
                                                         onupdate='CASCADE',
                                                         ondelete='CASCADE'))
    to_station: Mapped[int] = mapped_column(ForeignKey('station.id_station',
                                                       onupdate='CASCADE',
                                                       ondelete='CASCADE'))

    __table_args__ = (
        UniqueConstraint('id_bot_user', 'from_station', 'to_station',
                         name='favorite_unique'),
    )
