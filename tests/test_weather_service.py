from unittest.mock import MagicMock

from services.weather_service import WeatherService


def test_get_forecast_delegates_to_client():
    client = MagicMock()
    expected = {"hourly": {}, "daily": {}}
    client.get_forecast.return_value = expected

    result = WeatherService(client).get_forecast(30, -95)

    assert result == expected
    client.get_forecast.assert_called_once_with(30, -95)


def test_get_weather_series_maps_forecasts_to_points():
    client = MagicMock()
    client.get_forecast_batch.return_value = [
        {
            "hourly": {
                "time": ["2026-10-06T10:00", "2026-10-06T11:00"],
                "temperature_2m": [80, 82],
                "apparent_temperature": [81, 83],
                "precipitation": [0, 0.1],
                "relative_humidity_2m": [70, 68],
            }
        }
    ]

    series = WeatherService(client).get_weather_series([(30, -95)])

    assert len(series) == 1
    assert len(series[0]) == 2
    assert series[0][0].latitude == 30
    assert series[0][0].temperature == 80
    assert series[0][1].precipitation == 0.1


def test_get_weather_points_flattens_series():
    client = MagicMock()
    client.get_forecast_batch.return_value = [
        {
            "hourly": {
                "time": ["2026-10-06T10:00"],
                "temperature_2m": [80],
                "precipitation": [0],
                "relative_humidity_2m": [70],
            }
        },
        {
            "hourly": {
                "time": ["2026-10-06T10:00"],
                "temperature_2m": [81],
                "precipitation": [0.1],
                "relative_humidity_2m": [68],
            }
        },
    ]

    points = WeatherService(client).get_weather_points([(30, -95), (31, -94)])

    assert len(points) == 2
    assert [point.latitude for point in points] == [30, 31]


def test_get_weather_series_returns_empty_for_no_coordinates():
    client = MagicMock()
    assert WeatherService(client).get_weather_series([]) == []
    client.get_forecast_batch.assert_not_called()
