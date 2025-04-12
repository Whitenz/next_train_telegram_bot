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


@pytest.fixture
def schedules(
    populate_db: None,
    current_session: sessionmaker[Session] = db.sync_session,
) -> Sequence[models.Schedule]:
    statement = select(models.Schedule)
    with current_session() as session:
        return session.scalars(statement).all()
