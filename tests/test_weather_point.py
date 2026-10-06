from spatial.models import WeatherPoint


def test_weather_point_from_hourly():
    hourly = {
        "time": ["2026-10-06T10:00"],
        "temperature_2m": [80],
        "apparent_temperature": [81],
        "precipitation": [0.1],
        "precipitation_probability": [20],
        "relative_humidity_2m": [70],
        "weather_code": [2],
        "wind_speed_10m": [5],
        "wind_direction_10m": [180],
    }

    point = WeatherPoint.from_hourly(30, -95, hourly, 0)

    assert point.to_dict() == {
        "latitude": 30,
        "longitude": -95,
        "timestamp": "2026-10-06T10:00",
        "temperature": 80,
        "apparent_temperature": 81,
        "precipitation": 0.1,
        "precipitation_probability": 20,
        "humidity": 70,
        "weather_code": 2,
        "wind_speed": 5,
        "wind_direction": 180,
    }
