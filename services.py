import datetime as dt
import sqlite3
from typing import Any, List

# Get parameters for request to DB

from_station = 'mashinostroitelej'  # temporary hardcode
to_station = 'botanicheskaya'  # temporary hardcode
is_weekend = dt.datetime.today().weekday() > 4

# Connect to the SQLite database
conn = sqlite3.connect('schedule.db')


# Retrieve the closest time value from the database
def get_schedule(from_station: str = from_station,
                 to_station: str = to_station,
                 is_weekend: bool = is_weekend) -> list[Any]:

    cursor = conn.cursor()
    sql_query = f'''
        SELECT
          strftime(
            '%H:%M:%S',
            time(strftime('%s', departure_time) - strftime('%s', 'now', 'localtime'),
            'unixepoch')
          )
        FROM
          schedule
        WHERE
          from_station LIKE '{from_station}' AND
          to_station LIKE '{to_station}' AND
          is_weekend IS {is_weekend} AND
          departure_time > time('now', 'localtime')
        LIMIT
          2;
        '''
    cursor.execute(sql_query)

    return cursor.fetchall()

# Return time to the closest train and next

# message_closest_train = f'{closest_train[0]} (ч:мин:с)'
# message_next_train = f'{next_train[0]} (ч:мин:с)'
