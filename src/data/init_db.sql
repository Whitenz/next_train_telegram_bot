CREATE TABLE IF NOT EXISTS station (
    station_id SERIAL PRIMARY KEY,
    station_name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS schedule (
    schedule_id SERIAL PRIMARY KEY,
    from_station_id INTEGER NOT NULL,
    to_station_id INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    departure_time TIME NOT NULL,
    FOREIGN KEY (from_station_id) REFERENCES station(station_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (to_station_id) REFERENCES station(station_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT route_check CHECK (from_station_id != to_station_id),
    CONSTRAINT schedule_unique UNIQUE (from_station_id, to_station_id, is_weekend, departure_time)
);

CREATE TABLE IF NOT EXISTS bot_user (
    bot_user_id BIGINT PRIMARY KEY NOT NULL UNIQUE,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR,
    username VARCHAR,
    is_bot BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS favorite (
    favorite_id SERIAL PRIMARY KEY,
    bot_user_id INTEGER NOT NULL,
    from_station_id INTEGER NOT NULL,
    to_station_id INTEGER NOT NULL,
    FOREIGN KEY (bot_user_id) REFERENCES bot_user(bot_user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (from_station_id) REFERENCES station(station_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (to_station_id) REFERENCES station(station_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT favorite_unique UNIQUE (bot_user_id, from_station_id, to_station_id)
);
