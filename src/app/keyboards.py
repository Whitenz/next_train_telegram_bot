from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .orm_db import STATIONS_DICT

# Клавиатура с набором кнопок с названием станций
STATIONS_KEYBOARD = [
    [InlineKeyboardButton(station_name, callback_data=station_name)]
    for station_name in STATIONS_DICT.keys()
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
