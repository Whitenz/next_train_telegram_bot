import datetime as dt

import freezegun
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
    with freezegun.freeze_time(day):
        assert await utils.is_weekend() == expected


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
    current_dt = dt.datetime.now()
    with freezegun.freeze_time(current_dt.replace(hour=time.hour, minute=time.minute, second=time.second)):
        assert await utils.metro_is_closed() == expected
