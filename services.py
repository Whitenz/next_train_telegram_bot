import datetime as dt
import sqlite3

# Connect to the SQLite database
CONN = sqlite3.connect('schedule.db')


# Retrieve the closest time value from the database
def get_schedule(from_station: str, to_station: str) -> list[tuple]:
    is_weekend = dt.datetime.today().weekday() > 4
    cursor = CONN.cursor()
    sql_query = f'''
        SELECT
          strftime(
            '%H:%M:%S',
            time(strftime('%s', departure_time) - strftime('%s', 'now', 'localtime'),
            'unixepoch'
            )
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
