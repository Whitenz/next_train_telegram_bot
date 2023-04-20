"""Модуль содержит текстовые сообщения и команды, которые использует бот."""

# Команды, которые обрабатывает бот
START_COMMAND = 'start'
HELP_COMMAND = 'help'
SCHEDULE_COMMAND = 'schedule'
FAVORITES_COMMAND = 'favorites'
ADD_FAVORITE_COMMAND = 'add_favorite'
CLEAR_FAVORITES_COMMAND = 'clear_favorites'

# Текст сообщений для пользователя
START_TEXT = (
    'Привет {}!\n'
    'Бот знает расписание движения поездов в метро Екатеринбурга.'
)
HELP_TEXT = (
    'Команда /schedule показывает время до ближайших поездов. Для этого нужно'
    ' выбрать свою станцию, а затем направление движения поезда.\n\n'
    'Команда /favorites показывает время до ближайших поездов на избранных'
    ' маршрутах (не более двух).\n\n'
    'Команда /add_favorite и /clear_favorites добавляет выбранный маршрут в'
    ' список избранных маршрутов и очищает его соответственно. Добавить можно'
    ' не более двух маршрутов.'
)
METRO_IS_CLOSED_TEXT = (
    'Метрополитен закрыт. Часы работы с 06:00 до 00:00.\n'
    'Расписание будет доступно с 05:30.'
)
ADD_FAVORITES_TEXT = 'Маршрут "<b>{} ➡ {}</b>" добавлен в избранное.'
CLEAR_FAVORITES_TEXT = (
    'Список избранных маршрутов очищен.\n'
    'Чтобы добавить маршрут в избранное воспользуйтесь командой /add_favorite'
)
FAVORITES_LIMIT_REACHED_TEXT = (
    'У вас уже добавлено 2 маршрута в избранное и это максимум.'
)
WRONG_COMMAND_TEXT = 'Некорректная команда.'
CHOICE_STATION_TEXT = 'Выберите станцию отправления:'
CHOICE_DIRECTION_TEXT = 'Выберите конечную станцию направления:'
TEXT_WITH_TIME_TWO_TRAINS = (
    '<b>{direction}:</b>\n\n'
    'ближайший поезд через {time_to_train_1} (мин:с)\n'
    'следующий через {time_to_train_2} (мин:с)'
)
TEXT_WITH_TIME_ONE_TRAIN = (
    '<b>{direction}:</b>\n\n'
    'последний поезд через {time_to_train_1} (мин:с)'
)
TEXT_WITH_TIME_NONE = 'По расписанию поездов сегодня больше нет.'
CONVERSATION_TIMEOUT_TEXT = 'Время для выбора станций вышло.'
