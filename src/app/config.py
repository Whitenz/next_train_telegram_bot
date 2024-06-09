import datetime
import logging
from pathlib import (
    Path,
    PurePath,
)

import pydantic as p
import pydantic_settings as ps


class Settings(ps.BaseSettings):
    # env variables
    BOT_TOKEN: str
    DEVELOPER_TG_ID: int
    DB_DRIVERNAME_SYNC: str
    DB_DRIVERNAME_ASYNC: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    TZ: str
    MODE: str

    # path variables
    BASE_DIR: p.DirectoryPath = Path(__file__).parents[1]

    # logger params
    LOG_FILENAME: PurePath = PurePath.joinpath(BASE_DIR, 'data', 'bot.log')
    LOGGER_TEXT: str = 'Пользователь {first_name} ({id}) отправил команду "{command}"'

    # bot params
    OPEN_TIME_METRO: datetime.time = datetime.time(hour=5, minute=30)
    CLOSE_TIME_METRO: datetime.time = datetime.time(hour=0, minute=30)
    CHOICE_DIRECTION: int = p.Field(default=0, ge=0)
    FINAL_STAGE: int = p.Field(default=1, ge=0)
    CONVERSATION_TIMEOUT: int = p.Field(default=60 * 3, ge=60, le=3600)
    MAX_WAITING_TIME: int = p.Field(default=60, ge=15, le=60)
    LIMIT_ROW: int = p.Field(default=2, ge=1)
    LIMIT_FAVORITES: int = p.Field(default=2, ge=1)

    model_config = ps.SettingsConfigDict(
        env_file=(
            Path.joinpath(Path(__file__).parents[2], '.env.prod'),
            Path.joinpath(Path(__file__).parents[2], '.env.dev'),
        ),
        env_file_encoding='utf-8',
        extra="ignore",
    )


settings = Settings()

logging.basicConfig(
    filename=settings.LOG_FILENAME,
    format='[%(asctime)s] - [%(name)s] - [%(levelname)s] => %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S',
    level=logging.INFO,
    encoding='utf-8',
)
logging.getLogger('httpx').setLevel(logging.WARNING)
