from collections.abc import Sequence

import pytest
from src import (
    db,
    models,
)
from telegram import User

from .fixtures.bot_users import get_bot_users

SCHEDULES_LEN = 4584


class TestSchedule:
    def test_count_schedule(self, schedules: Sequence[models.Schedule]) -> None:
        assert len(schedules) == SCHEDULES_LEN, f"В таблице с расписанием должно быть {SCHEDULES_LEN} записи."

    def test_schedule_type(self, schedules: Sequence[models.Schedule]) -> None:
        assert all(isinstance(schedule, models.Schedule) for schedule in schedules), (
            "Объекты должны быть экземплярами класса Schedule."
        )

    @pytest.mark.asyncio
    async def test_select_schedule(self) -> None:
        schedules = await db.select_schedule(from_station_id=1, to_station_id=9)

        assert isinstance(schedules, list)
        assert all(isinstance(schedule, models.Schedule) for schedule in schedules), (
            "Объекты должны быть экземплярами класса Schedule."
        )


class TestBotUser:
    @pytest.mark.asyncio
    async def test_insert_user(self, new_telegram_user: User) -> None:
        bot_users = get_bot_users()
        assert len(bot_users) == 0, "Изначально таблица bot_user должна быть пустая."

        await db.insert_user(new_telegram_user)

        bot_users = get_bot_users()
        assert len(bot_users) == 1, "В таблице bot_user не появился новый пользователь."
        assert bot_users[0].bot_user_id == new_telegram_user.id
        assert bot_users[0].first_name == new_telegram_user.first_name
        assert bot_users[0].last_name == new_telegram_user.last_name
        assert bot_users[0].username == new_telegram_user.username
        assert bot_users[0].is_bot == new_telegram_user.is_bot

    @pytest.mark.asyncio
    async def test_select_all_users(self, async_session_fixture) -> None:
        """Test that we can select all users from database."""
        # Get initial count
        initial_users = await db.select_all_users()
        initial_count = len(initial_users)

        # Create some test users
        user1 = models.BotUser(
            bot_user_id=111,
            first_name="Test1",
            last_name=None,
            username="test1",
            is_bot=False,
        )
        user2 = models.BotUser(
            bot_user_id=222,
            first_name="Test2",
            last_name=None,
            username="test2",
            is_bot=False,
        )
        async_session_fixture.add(user1)
        async_session_fixture.add(user2)
        await async_session_fixture.commit()

        # Test the function
        users = await db.select_all_users()

        assert len(users) == initial_count + 2
        user_ids = [u.bot_user_id for u in users]
        assert 111 in user_ids
        assert 222 in user_ids

    @pytest.mark.asyncio
    async def test_delete_user(self, async_session_fixture) -> None:
        """Test that we can delete a user from database."""
        # Create a test user
        user = models.BotUser(
            bot_user_id=999,
            first_name="ToDelete",
            last_name=None,
            username="to_delete",
            is_bot=False,
        )
        async_session_fixture.add(user)
        await async_session_fixture.commit()

        # Verify user exists
        users_before = await db.select_all_users()
        user_ids_before = [u.bot_user_id for u in users_before]
        assert 999 in user_ids_before

        # Delete the user
        result = await db.delete_user(999)
        assert result is True

        # Verify user is deleted
        users_after = await db.select_all_users()
        user_ids_after = [u.bot_user_id for u in users_after]
        assert 999 not in user_ids_after

        # Try deleting non-existent user
        result2 = await db.delete_user(999)
        assert result2 is False
