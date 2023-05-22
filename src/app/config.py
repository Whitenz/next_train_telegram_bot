import datetime
import logging
import os
from pathlib import Path

from pydantic import BaseSettings, DirectoryPath, PostgresDsn, conint


class Settings(BaseSettings):
    BOT_TOKEN: str
    PG_DSN_SYNC: PostgresDsn
    PG_DSN_ASYNC: PostgresDsn
    BASE_DIR: DirectoryPath = os.path.dirname(os.path.dirname(__file__))
    LOG_FILENAME: Path = os.path.join(BASE_DIR, 'data', 'bot.log')
    LOGGER_TEXT: str = (
        'Пользователь {first_name} ({id_bot_user}) отправил команду "{command}"'
    )
    OPEN_TIME_METRO: datetime.time = datetime.time(hour=5, minute=30)
    CLOSE_TIME_METRO: datetime.time = datetime.time(hour=0, minute=30)
    CHOICE_DIRECTION: conint(ge=0) = 0
    FINAL_STAGE: conint(ge=0) = 1
    CONVERSATION_TIMEOUT: conint(ge=60, le=3600) = 60 * 3
    MAX_WAITING_TIME: conint(ge=15, le=60) = 60  # minutes
    LIMIT_ROW: conint(ge=1) = 2
    LIMIT_FAVORITES: conint(ge=1) = 2

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        env_file_encoding = 'utf-8'


settings = Settings()

logging.basicConfig(
    filename=settings.LOG_FILENAME,
    format='[%(asctime)s] - [%(name)s] - [%(levelname)s] => %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S',
    level=logging.INFO,
    encoding='utf-8'
)
