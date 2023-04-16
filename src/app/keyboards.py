from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .db import get_stations_from_db

# Клавиатура с набором кнопок с названием станций
STATIONS_KEYBOARD = [
    [InlineKeyboardButton(name_station, callback_data=name_station)]
    for _, name_station in get_stations_from_db()
]
STATIONS_REPLY_MARKUP = InlineKeyboardMarkup(STATIONS_KEYBOARD)

# Клавиатура с набором кнопок конечных станций-направлений
FIRST_STATION_BUTTON = STATIONS_KEYBOARD[0][0]
LAST_STATION_BUTTON = STATIONS_KEYBOARD[-1][0]
DIRECTION_KEYBOARD = [[FIRST_STATION_BUTTON, LAST_STATION_BUTTON]]
DIRECTION_REPLY_MARKUP = InlineKeyboardMarkup(DIRECTION_KEYBOARD)

# Словарь для выбора направления на конечных станциях, где 'from_station' ключ,
# а 'to_station' значение (добавлен, т.к. нет смысла выбирать пользователю)
END_STATION_DIRECTION = {
    FIRST_STATION_BUTTON.text: LAST_STATION_BUTTON.text,
    LAST_STATION_BUTTON.text: FIRST_STATION_BUTTON.text,
}
