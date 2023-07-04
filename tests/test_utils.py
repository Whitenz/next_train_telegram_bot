import datetime as dt

import pytest

from src.app import utils
from src.app.config import settings


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'day, expected',
    [
        (dt.datetime(2023, 5, 27, 12, 0, 0), True),
        (dt.datetime(2023, 5, 29, 12, 0, 0), False),
    ]
)
async def test_is_weekend(day, expected):
    assert await utils.is_weekend(day) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'time, expected',
    [
        (settings.OPEN_TIME_METRO, False),
        (settings.CLOSE_TIME_METRO, True),
        (dt.time(hour=0, minute=29), False),
        (dt.time(hour=5, minute=29), True),

    ]
)
async def test_metro_is_closed(time, expected):
    assert await utils.metro_is_closed(time) == expected
