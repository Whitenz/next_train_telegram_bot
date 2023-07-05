import asyncio
from pathlib import PurePath

import pytest
from sqlalchemy import text

from app.config import settings
from src.app.db import sync_engine, sync_session
from src.app.models import Base
from tests.fixtures.schedules import schedules
from tests.fixtures.bot_users import new_telegram_user

__all__ = [
    'schedules',
    'new_telegram_user',
]


@pytest.fixture(scope='session')
def check_test_mode():
    assert settings.MODE == 'test'


@pytest.fixture(scope='session', autouse=True)
def init_db(check_test_mode):
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)


@pytest.fixture(scope='session')
def sql_commands():
    sql_commands_file = PurePath.joinpath(settings.BASE_DIR, 'data', 'populate_db.sql')
    with open(sql_commands_file) as f:
        sql_commands = f.read().split('\n\n')
    return sql_commands


@pytest.fixture(scope='session')
def populate_db(sql_commands: list[str]):
    with sync_session() as session:
        for command in sql_commands:
            session.execute(text(command))
        session.commit()


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()
