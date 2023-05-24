from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.db import STATIONS_DICT

# Клавиатура с набором кнопок с названием станций
STATIONS_KEYBOARD = [
    [InlineKeyboardButton(station_name, callback_data=station_id)]
    for station_id, station_name in STATIONS_DICT.items()
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
    FIRST_STATION_BUTTON.callback_data: LAST_STATION_BUTTON.callback_data,
    LAST_STATION_BUTTON.callback_data: FIRST_STATION_BUTTON.callback_data,
}
