from datetime import datetime
from unittest.mock import MagicMock

from weather_ingestion import WeatherIngestion


def forecast():
    return {
        "hourly": {
            "time": [
                "2026-10-06T10:00",
                "2026-10-06T11:00",
                "2026-10-06T12:00",
            ],
            "temperature_2m": [80.0, 82.0, 84.0],
            "precipitation": [0.0, 0.1, 0.2],
            "relative_humidity_2m": [70.0, 68.0, 65.0],
        }
    }


def test_run_processes_locations_and_returns_summary():
    database = MagicMock()
    database.get_watermark.return_value = None
    client = MagicMock()
    client.get_forecast.return_value = forecast()

    locations = [
        {"name": "Spring, TX", "latitude": 30.0799, "longitude": -95.4172},
        {"name": "Houston, TX", "latitude": 29.7604, "longitude": -95.3698},
    ]

    result = WeatherIngestion(database, client, locations).run()

    assert result == {
        "locations_processed": 2,
        "locations_failed": 0,
        "records_processed": 6,
    }
    assert database.commit.call_count == 2


def test_run_continues_after_one_location_fails():
    database = MagicMock()
    database.get_watermark.return_value = None
    client = MagicMock()
    client.get_forecast.side_effect = [
        RuntimeError("API failure"),
        forecast(),
    ]

    locations = [
        {"name": "Spring, TX", "latitude": 30.0799, "longitude": -95.4172},
        {"name": "Houston, TX", "latitude": 29.7604, "longitude": -95.3698},
    ]

    result = WeatherIngestion(database, client, locations).run()

    assert result["locations_processed"] == 1
    assert result["locations_failed"] == 1
    assert result["records_processed"] == 3
    database.rollback.assert_called_once()


def test_process_location_refreshes_existing_window():
    database = MagicMock()
    database.get_location_id.return_value = 1
    database.get_watermark.return_value = "2026-10-06T12:00"
    client = MagicMock()
    client.get_forecast.return_value = forecast()

    ingestion = WeatherIngestion(
        database,
        client,
        [{"name": "Spring, TX", "latitude": 30.0799, "longitude": -95.4172}],
    )

    records = ingestion._process_location(ingestion.locations[0])

    assert records == 3
    assert database.save_weather.call_count == 3
    assert datetime.fromisoformat(database.save_weather.call_args_list[0].args[1]) == datetime(2026, 10, 6, 10)
