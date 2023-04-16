import datetime as dt
from dataclasses import dataclass


@dataclass
class Schedule:
    from_station: str
    to_station: str
    time_to_train: str

    def __post_init__(self):
        datetime_obj = dt.datetime.strptime(self.time_to_train, '%H:%M:%S')
        self.time_to_train = datetime_obj.strftime('%M:%S')

    @property
    def direction(self):
        return f'{self.from_station} ➡ {self.to_station}'
