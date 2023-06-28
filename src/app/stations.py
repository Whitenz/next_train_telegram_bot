from functools import lru_cache

from app.db import get_stations


@lru_cache
def get_stations_dict() -> dict[int, str]:
    """
    Функция генерирует словарь со всеми станциями в БД.
    Словарь генерирует при первом вызове функции, а затем возвращается кэш.
    Ключом словаря является station_id, а значения station_name. При последующи

    Returns:
        dict[int, str]
    """
    return {Station.station_id: Station.station_name for Station in get_stations()}
