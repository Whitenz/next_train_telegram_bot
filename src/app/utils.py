import datetime as dt

from app.config import settings


async def is_weekend() -> bool:
    """Функция проверяет выходной сейчас день или нет."""
    today = dt.datetime.now()
    delta = dt.timedelta(minutes=30)
    return (today - delta).isoweekday() > 5


async def metro_is_closed() -> bool:
    """Функция проверяет закрыто ли метро в соответствии с часами работы."""
    now_time = dt.datetime.now().time()
    return settings.CLOSE_TIME_METRO <= now_time <= settings.OPEN_TIME_METRO
