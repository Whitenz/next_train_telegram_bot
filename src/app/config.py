import datetime
import logging
from pathlib import Path, PurePath

from pydantic import BaseSettings, DirectoryPath, conint


class Settings(BaseSettings):
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
    BASE_DIR: DirectoryPath = Path(__file__).parents[1]

    # logger params
    LOG_FILENAME: PurePath = PurePath.joinpath(BASE_DIR, 'data', 'bot.log')
    LOGGER_TEXT: str = 'Пользователь {first_name} ({id}) отправил команду "{command}"'

    # bot params
    OPEN_TIME_METRO: datetime.time = datetime.time(hour=5, minute=30)
    CLOSE_TIME_METRO: datetime.time = datetime.time(hour=0, minute=30)
    CHOICE_DIRECTION: conint(ge=0) = 0
    FINAL_STAGE: conint(ge=0) = 1
    CONVERSATION_TIMEOUT: conint(ge=60, le=3600) = 60 * 3
    MAX_WAITING_TIME: conint(ge=15, le=60) = 60  # minutes
    LIMIT_ROW: conint(ge=1) = 2
    LIMIT_FAVORITES: conint(ge=1) = 2

    class Config:
        env_file: PurePath = (
            PurePath.joinpath(Path(__file__).parents[2], '.env.prod'),
            PurePath.joinpath(Path(__file__).parents[2], '.env.dev')
        )
        env_file_encoding: str = 'utf-8'


settings = Settings()

logging.basicConfig(
    filename=settings.LOG_FILENAME,
    format='[%(asctime)s] - [%(name)s] - [%(levelname)s] => %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S',
    level=logging.INFO,
    encoding='utf-8'
)
logging.getLogger('httpx').setLevel(logging.WARNING)
