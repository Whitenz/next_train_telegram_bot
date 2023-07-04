from app.stations import get_stations_dict


def test_get_stations_dict(init_db):
    stations_dict = get_stations_dict()
    assert type(stations_dict) == dict
    assert len(stations_dict) == 9
    assert all(type(key) == int for key in stations_dict.keys())
    assert all(type(value) == str for value in stations_dict.values())
