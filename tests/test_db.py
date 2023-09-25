import pytest

from app import db, models
from tests.fixtures.bot_users import get_bot_users


@pytest.mark.usefixtures('schedules')
class TestSchedule:
    def test_count_schedule(self, schedules):
        assert len(schedules) == 4572, 'В таблице с расписанием должно быть 4572 записи.'

    def test_schedule_type(self, schedules):
        assert all(type(schedule) == models.Schedule for schedule in schedules), (
                'Объекты должны быть экземплярами класса Schedule.'
        )

    @pytest.mark.asyncio
    async def test_select_schedule(self):
        schedules = await db.select_schedule(from_station_id=1, to_station_id=9)

        assert type(schedules) == list
        assert all(type(schedule) == models.Schedule for schedule in schedules), (
                'Объекты должны быть экземплярами класса Schedule.'
        )


class TestBotUser:
    @pytest.mark.asyncio
    async def test_insert_user(self, new_telegram_user):
        bot_users = get_bot_users()
        assert len(bot_users) == 0, 'Изначально таблица bot_user должна быть пустая.'

        await db.insert_user(new_telegram_user)

        bot_users = get_bot_users()
        assert len(bot_users) == 1, 'В таблице bot_user не появился новый пользователь.'
        assert bot_users[0].bot_user_id == new_telegram_user.id
        assert bot_users[0].first_name == new_telegram_user.first_name
        assert bot_users[0].last_name == new_telegram_user.last_name
        assert bot_users[0].username == new_telegram_user.username
        assert bot_users[0].is_bot == new_telegram_user.is_bot
