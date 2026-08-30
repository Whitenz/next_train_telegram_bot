import socket
from collections.abc import Generator
from pathlib import PurePath
from typing import (
    Any,
)

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from src.config import settings
from src.db import (
    async_session,
    sync_engine,
    sync_session,
)
from src.models import Base
from testcontainers.community.postgres import PostgresContainer

from .fixtures.bot_users import new_telegram_user
from .fixtures.schedules import schedules

__all__ = [
    "async_session_fixture",
    "new_telegram_user",
    "populate_db",
    "schedules",
]


def _port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex((host, port)) == 0


@pytest.fixture(scope="session")
def postgres_container(check_test_mode: None) -> Generator[str, Any, None]:
    """Поднимает тестовый postgres, если порт из настроек свободен.

    Движки в src.db создаются на импорте из .env.test, поэтому контейнер
    привязывается к фиксированному settings.DB_PORT. Если порт уже слушается
    (например, поднят db из docker compose), используется существующий сервер.
    """
    if _port_is_open(settings.DB_HOST, settings.DB_PORT):
        yield "external"
        return

    container = PostgresContainer(
        "postgres:15.10-alpine",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.DB_NAME,
    ).with_bind_ports(5432, settings.DB_PORT)
    container.start()
    try:
        yield "container"
    finally:
        container.stop()


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
def init_db(check_test_mode: None, postgres_container: str) -> Generator[None, Any, None]:
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
