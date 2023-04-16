from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .db import get_stations_from_db

STATIONS_KEYBOARD = [
    [InlineKeyboardButton(name_station, callback_data=name_station)]
    for _, name_station in get_stations_from_db()
]
STATIONS_REPLY_MARKUP = InlineKeyboardMarkup(STATIONS_KEYBOARD)
FIRST_STATION_BUTTON = STATIONS_KEYBOARD[0][0]
LAST_STATION_BUTTON = STATIONS_KEYBOARD[-1][0]
DIRECTION_KEYBOARD = [[FIRST_STATION_BUTTON, LAST_STATION_BUTTON]]
DIRECTION_REPLY_MARKUP = InlineKeyboardMarkup(DIRECTION_KEYBOARD)
