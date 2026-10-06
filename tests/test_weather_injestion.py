from unittest.mock import MagicMock

from weather_database import WeatherDatabase
from weather_ingestion import WeatherIngestion


def create_client(weather_data):
    client = MagicMock()

    client.get_forecast.return_value = {"hourly": weather_data}

    return client


def create_location():
    return {
        "name": "Spring, TX",
        "latitude": 30.0799,
        "longitude": -95.4172,
    }


def test_ingestion_saves_new_weather_data(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)
    database.create_tables()

    client = create_client(
        {
            "time": [
                "2026-10-05T10:00",
                "2026-10-05T11:00",
            ],
            "temperature_2m": [
                80.0,
                82.0,
            ],
            "precipitation": [
                0.0,
                0.1,
            ],
            "relative_humidity_2m": [
                70.0,
                68.0,
            ],
        }
    )

    location = create_location()

    ingestion = WeatherIngestion(
        database,
        client,
        [location],
    )

    ingestion.run()

    location_id = database.get_location_id("Spring, TX")

    database.cursor.execute(
        """
        SELECT timestamp, temperature, precipitation, humidity
        FROM weather
        WHERE location_id = ?
        ORDER BY timestamp
        """,
        (location_id,),
    )

    results = database.cursor.fetchall()

    assert results == [
        ("2026-10-05T10:00", 80.0, 0.0, 70.0),
        ("2026-10-05T11:00", 82.0, 0.1, 68.0),
    ]

    client.get_forecast.assert_called_once_with(
        latitude=30.0799,
        longitude=-95.4172,
    )

    database.close()


def test_ingestion_skips_existing_records(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)
    database.create_tables()

    database.add_location(
        "Spring, TX",
        30.0799,
        -95.4172,
    )

    location_id = database.get_location_id("Spring, TX")

    database.save_weather(
        location_id,
        "2026-10-05T10:00",
        80.0,
        0.0,
        70.0,
    )

    database.save_weather(
        location_id,
        "2026-10-05T11:00",
        82.0,
        0.1,
        68.0,
    )

    database.commit()

    client = create_client(
        {
            "time": [
                "2026-10-05T10:00",
                "2026-10-05T11:00",
                "2026-10-05T12:00",
            ],
            "temperature_2m": [
                80.0,
                82.0,
                85.0,
            ],
            "precipitation": [
                0.0,
                0.1,
                0.2,
            ],
            "relative_humidity_2m": [
                70.0,
                68.0,
                65.0,
            ],
        }
    )

    ingestion = WeatherIngestion(
        database,
        client,
        [create_location()],
    )

    ingestion.run()

    database.cursor.execute(
        """
        SELECT timestamp, temperature, precipitation, humidity
        FROM weather
        WHERE location_id = ?
        ORDER BY timestamp
        """,
        (location_id,),
    )

    results = database.cursor.fetchall()

    assert results == [
        ("2026-10-05T10:00", 80.0, 0.0, 70.0),
        ("2026-10-05T11:00", 82.0, 0.1, 68.0),
        ("2026-10-05T12:00", 85.0, 0.2, 65.0),
    ]

    database.close()


def test_ingestion_handles_multiple_locations(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)
    database.create_tables()

    locations = [
        {
            "name": "Spring, TX",
            "latitude": 30.0799,
            "longitude": -95.4172,
        },
        {
            "name": "Houston, TX",
            "latitude": 29.7604,
            "longitude": -95.3698,
        },
    ]

    client = MagicMock()

    client.get_forecast.side_effect = [
        {
            "hourly": {
                "time": ["2026-10-05T10:00"],
                "temperature_2m": [80.0],
                "precipitation": [0.0],
                "relative_humidity_2m": [70.0],
            }
        },
        {
            "hourly": {
                "time": ["2026-10-05T10:00"],
                "temperature_2m": [81.0],
                "precipitation": [0.1],
                "relative_humidity_2m": [68.0],
            }
        },
    ]

    ingestion = WeatherIngestion(
        database,
        client,
        locations,
    )

    ingestion.run()

    database.cursor.execute("SELECT COUNT(*) FROM locations")

    assert database.cursor.fetchone()[0] == 2

    database.cursor.execute("SELECT COUNT(*) FROM weather")

    assert database.cursor.fetchone()[0] == 2

    assert client.get_forecast.call_count == 2

    database.close()


def test_ingestion_does_not_insert_data_at_or_before_watermark(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)
    database.create_tables()

    database.add_location(
        "Spring, TX",
        30.0799,
        -95.4172,
    )

    location_id = database.get_location_id("Spring, TX")

    database.save_weather(
        location_id,
        "2026-10-05T12:00",
        85.0,
        0.2,
        65.0,
    )

    database.commit()

    client = create_client(
        {
            "time": [
                "2026-10-05T10:00",
                "2026-10-05T11:00",
                "2026-10-05T12:00",
            ],
            "temperature_2m": [
                80.0,
                82.0,
                85.0,
            ],
            "precipitation": [
                0.0,
                0.1,
                0.2,
            ],
            "relative_humidity_2m": [
                70.0,
                68.0,
                65.0,
            ],
        }
    )

    ingestion = WeatherIngestion(
        database,
        client,
        [create_location()],
    )

    ingestion.run()

    database.cursor.execute(
        """
        SELECT COUNT(*)
        FROM weather
        WHERE location_id = ?
        """,
        (location_id,),
    )

    assert database.cursor.fetchone()[0] == 1

    database.close()


def test_ingestion_creates_location_if_missing(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)
    database.create_tables()

    client = create_client(
        {
            "time": [],
            "temperature_2m": [],
            "precipitation": [],
            "relative_humidity_2m": [],
        }
    )

    ingestion = WeatherIngestion(
        database,
        client,
        [create_location()],
    )

    ingestion.run()

    location_id = database.get_location_id("Spring, TX")

    assert location_id is not None

    database.close()
