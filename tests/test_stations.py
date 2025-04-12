from collections.abc import Generator
from typing import (
    Any,
)

from src.stations import get_stations_dict

COUNT_STATIONS = 9


def test_get_stations_dict(init_db: Generator[None, Any, None]) -> None:
    stations_dict = get_stations_dict()
    assert len(stations_dict) == COUNT_STATIONS
    assert type(stations_dict) is dict
    assert all(type(key) is int for key in stations_dict)
    assert all(type(value) is str for value in stations_dict.values())
