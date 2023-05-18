import datetime as dt

from .config import CLOSE_TIME_METRO, OPEN_TIME_METRO
from .messages import (TEXT_WITH_TIME_NONE, TEXT_WITH_TIME_ONE_TRAIN,
                       TEXT_WITH_TIME_TWO_TRAINS)


async def is_weekend() -> bool:
    """Функция проверяет выходной сейчас день или нет."""
    today = dt.datetime.now()
    delta = dt.timedelta(minutes=30)
    return (today - delta).isoweekday() > 5


async def metro_is_closed() -> bool:
    """Функция проверяет закрыто ли метро в соответствии с часами работы."""
    return CLOSE_TIME_METRO <= dt.datetime.now().time() <= OPEN_TIME_METRO


async def format_text_with_time_to_train(schedules):
    if len(schedules) >= 2:
        return TEXT_WITH_TIME_TWO_TRAINS.format(
            direction=schedules[0].direction,
            time_to_train_1=schedules[0].time_to_train.strftime('%M:%S'),
            time_to_train_2=schedules[1].time_to_train.strftime('%M:%S'),

        )
    if len(schedules) == 1:
        return TEXT_WITH_TIME_ONE_TRAIN.format(
            direction=schedules[0].direction,
            time_to_train_1=schedules[0].time_to_train.strftime('%M:%S')
        )
    return TEXT_WITH_TIME_NONE
