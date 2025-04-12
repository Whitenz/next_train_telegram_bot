import datetime as dt

from app.config import settings


async def is_weekend() -> bool:
    """Функция проверяет, является ли текущий день выходным.

    Returns:
        True, если текущий день является выходным (суббота или воскресенье);
          False в противном случае.
    """
    return (dt.datetime.now() - dt.timedelta(minutes=30)).isoweekday() > 5


async def metro_is_closed() -> bool:
    """Функция проверяет, закрыт ли метрополитен в соответствии с часами работы.

    Returns:
        True, если метро закрыто в настоящее время. Иначе False.
    """
    return settings.CLOSE_TIME_METRO <= dt.datetime.now().time() < settings.OPEN_TIME_METRO
