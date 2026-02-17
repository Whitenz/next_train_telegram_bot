from collections.abc import Generator
from pathlib import PurePath
from typing import (
    Any,
)

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from src.config import settings
from src.db import (
    async_engine,
    async_session,
    sync_engine,
    sync_session,
)
from src.models import Base

from .fixtures.bot_users import new_telegram_user
from .fixtures.schedules import schedules

__all__ = [
    "new_telegram_user",
    "schedules",
]


@pytest.fixture
async def async_session_fixture() -> AsyncSession:
    """Create an async session for testing."""
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="session")
def check_test_mode() -> None:
    assert settings.MODE == "test"


@pytest.fixture(scope="session", autouse=True)
def init_db(check_test_mode: None) -> Generator[None, Any, None]:
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)


@pytest.fixture(scope="session")
def sql_commands() -> list[str]:
    sql_commands_file = PurePath.joinpath(settings.BASE_DIR, "data", "populate_db.sql")
    with sql_commands_file.open("r") as f:
        return f.read().split("\n\n")


@pytest.fixture(scope="session")
def populate_db(sql_commands: list[str]) -> None:
    with sync_session() as session:
        for command in sql_commands:
            session.execute(text(command))
        session.commit()
