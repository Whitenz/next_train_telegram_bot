import datetime as dt

from app.config import settings


async def is_weekend(day: dt.datetime = dt.datetime.now()) -> bool:
    """Функция проверяет, является ли текущий день выходным.

    Args:
        day: день для проверки, экземпляр класса datetime.datetime

    Returns:
        True, если текущий день является выходным (суббота или воскресенье);
          False в противном случае.
    """
    delta = dt.timedelta(minutes=30)
    return (day - delta).isoweekday() > 5


async def metro_is_closed(time: dt.time = dt.datetime.now().time()) -> bool:
    """Функция проверяет, закрыт ли метрополитен в соответствии с часами работы.

    Args:
        time: время для проверки, экземпляр класса datetime.time

    Returns:
        True, если метро закрыто в настоящее время. Иначе False.
    """
    return settings.CLOSE_TIME_METRO <= time < settings.OPEN_TIME_METRO
