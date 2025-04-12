from collections.abc import Sequence

import pytest
from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from src import (
    db,
    models,
)
from telegram import User


def get_bot_users(current_session: sessionmaker[Session] = db.sync_session) -> Sequence[models.BotUser]:
    statement = select(models.BotUser)
    with current_session() as session:
        return session.scalars(statement).all()


@pytest.fixture
def new_telegram_user() -> User:
    return User(id=123456789, first_name="Ilya", is_bot=False, last_name="Kolesnikov", username="ilya_klsnkv")
