import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app import db, models


@pytest.fixture
def schedules(populate_db, current_session: sessionmaker[Session] = db.sync_session):
    statement = select(models.Schedule)
    with current_session() as session:
        schedules = session.scalars(statement).all()
    return schedules
