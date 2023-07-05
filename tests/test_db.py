import pytest

from app.db import select_schedule, sync_session
from app.models import Schedule

from sqlalchemy import select


@pytest.fixture(scope='session')
def schedules(populate_db):
    statement = select(Schedule)
    with sync_session() as session:
        schedules = session.scalars(statement).all()
    return schedules


@pytest.mark.usefixtures('schedules')
class TestSchedule:
    def test_count_schedule(self, schedules):
        assert len(schedules) == 4572, 'В таблице с расписанием должно быть 4572 записи.'

    def test_schedule_type(self, schedules):
        assert all(type(schedule) == Schedule for schedule in schedules), (
                'Объекты должны быть экземплярами класса Schedule.'
        )

    @pytest.mark.asyncio
    async def test_select_schedule(self):
        schedules = await select_schedule(from_station_id=1, to_station_id=9)

        assert type(schedules) == list
        assert all(type(schedule) == Schedule for schedule in schedules), (
                'Объекты должны быть экземплярами класса Schedule.'
        )
