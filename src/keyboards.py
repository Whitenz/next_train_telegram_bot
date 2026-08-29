from functools import lru_cache

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from . import bot_commands
from .stations import get_stations_dict


@lru_cache(maxsize=1)
def get_stations_keyboard() -> list[list[InlineKeyboardButton]]:
    """Клавиатура с набором кнопок с названием станций.

    Собирается при первом обращении, чтобы не делать запрос к БД в момент импорта модуля.
    """
    return [
        [InlineKeyboardButton(station_name, callback_data=str(station_id))]
        for station_id, station_name in get_stations_dict().items()
    ]


@lru_cache(maxsize=1)
def get_stations_reply_markup() -> InlineKeyboardMarkup:
    """Разметка клавиатуры выбора станции отправления."""
    return InlineKeyboardMarkup(get_stations_keyboard())


@lru_cache(maxsize=1)
def get_direction_reply_markup() -> InlineKeyboardMarkup:
    """Разметка клавиатуры с набором кнопок конечных станций-направлений."""
    stations_keyboard = get_stations_keyboard()
    first_station_button = stations_keyboard[0][0]
    last_station_button = stations_keyboard[-1][0]
    return InlineKeyboardMarkup([[first_station_button, last_station_button]])


@lru_cache(maxsize=1)
def get_end_station_direction() -> dict[int, int]:
    """Словарь для выбора направления на конечных станциях, где 'from_station' ключ,
    а 'to_station' значение (добавлен, т.к. нет смысла выбирать пользователю).
    """
    station_ids = list(get_stations_dict())
    first_station_id = station_ids[0]
    last_station_id = station_ids[-1]
    return {
        first_station_id: last_station_id,
        last_station_id: first_station_id,
    }


# Клавиатура подтверждения рассылки (не зависит от БД, поэтому остаётся константой)
BROADCAST_CONFIRM_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("✅ Отправить", callback_data=bot_commands.BROADCAST_CONFIRM_CALLBACK),
            InlineKeyboardButton("❌ Отмена", callback_data=bot_commands.BROADCAST_CANCEL_CALLBACK),
        ]
    ]
)
