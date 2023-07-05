import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from telegram import User

from app import db, models


def get_bot_users(current_session: sessionmaker[Session] = db.sync_session):
    statement = select(models.BotUser)
    with current_session() as session:
        return session.scalars(statement).all()


@pytest.fixture
def new_telegram_user():
    return User(
        id=123456789,
        first_name='Ilya',
        is_bot=False,
        last_name='Kolesnikov',
        username='ilya_klsnkv'
    )
