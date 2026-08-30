from collections.abc import Sequence

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
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
    async def test_select_all_users(self, async_session_fixture: AsyncSession) -> None:
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
    async def test_delete_user(self, async_session_fixture: AsyncSession) -> None:
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

    @pytest.mark.asyncio
    async def test_delete_user_cascades_favorites(self, async_session_fixture: AsyncSession, populate_db: None) -> None:
        """Test that deleting a user cascades to their favorite routes."""
        # Create a test user
        user = models.BotUser(
            bot_user_id=888,
            first_name="CascadeUser",
            last_name=None,
            username="cascade_user",
            is_bot=False,
        )
        async_session_fixture.add(user)
        await async_session_fixture.commit()

        # Create favorite routes for the user
        favorite1 = models.Favorite(
            bot_user_id=888,
            from_station_id=1,
            to_station_id=9,
        )
        favorite2 = models.Favorite(
            bot_user_id=888,
            from_station_id=2,
            to_station_id=8,
        )
        async_session_fixture.add(favorite1)
        async_session_fixture.add(favorite2)
        await async_session_fixture.commit()

        # Verify favorites exist
        favorites_before = await async_session_fixture.execute(
            db.select(models.Favorite).where(models.Favorite.bot_user_id == 888)
        )
        favorites_count_before = len(favorites_before.scalars().all())
        assert favorites_count_before == 2, "User should have 2 favorite routes"

        # Delete the user
        result = await db.delete_user(888)
        assert result is True, "User deletion should succeed"

        # Verify user is deleted
        users_after = await db.select_all_users()
        user_ids_after = [u.bot_user_id for u in users_after]
        assert 888 not in user_ids_after, "User should be deleted"

        # Verify favorites are cascade deleted
        favorites_after = await async_session_fixture.execute(
            db.select(models.Favorite).where(models.Favorite.bot_user_id == 888)
        )
        favorites_count_after = len(favorites_after.scalars().all())
        assert favorites_count_after == 0, "All favorite routes should be cascade deleted"

    @pytest.mark.asyncio
    async def test_delete_users(self, async_session_fixture: AsyncSession, populate_db: None) -> None:
        """Test batch deletion of users by their ids."""
        user1 = models.BotUser(
            bot_user_id=777,
            first_name="Batch1",
            last_name=None,
            username="batch1",
            is_bot=False,
        )
        user2 = models.BotUser(
            bot_user_id=778,
            first_name="Batch2",
            last_name=None,
            username="batch2",
            is_bot=False,
        )
        async_session_fixture.add(user1)
        async_session_fixture.add(user2)
        await async_session_fixture.commit()

        deleted_count = await db.delete_users([777, 778])

        assert deleted_count == 2
        users_after = await db.select_all_users()
        user_ids_after = [u.bot_user_id for u in users_after]
        assert 777 not in user_ids_after
        assert 778 not in user_ids_after

    @pytest.mark.asyncio
    async def test_delete_users_empty_list(self) -> None:
        """Test that batch deletion with empty list deletes nothing."""
        deleted_count = await db.delete_users([])

        assert deleted_count == 0
