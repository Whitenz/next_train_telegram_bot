import datetime as dt
import sqlite3

# Get parameters for request to DB

from_station = 'mashinostroitelej'  # temporary hardcode
to_station = 'botanicheskaya'  # temporary hardcode
is_weekend = dt.datetime.today().weekday() > 4

# Connect to the SQLite database
conn = sqlite3.connect('schedule.db')

# Retrieve the closest time value from the database
cursor = conn.cursor()
sql_query = f'''
    SELECT
      departure_time
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

# Return time to the closest train and next
closest_train, next_train = cursor.fetchall()

print(closest_train[0])
print(next_train[0])


