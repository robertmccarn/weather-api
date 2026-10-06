from weather_database import WeatherDatabase


def test_create_tables(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)

    database.create_tables()

    database.cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    )

    tables = {row[0] for row in database.cursor.fetchall()}

    assert "locations" in tables
    assert "weather" in tables

    database.close()


def test_add_location(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)

    database.create_tables()
    database.add_location(
        "Spring, TX",
        30.0799,
        -95.4172,
    )

    location_id = database.get_location_id("Spring, TX")

    assert location_id is not None

    database.close()


def test_get_location_id_raises_when_location_not_found(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)

    database.create_tables()

    try:
        database.get_location_id("Unknown")
        assert False
    except ValueError as error:
        assert str(error) == "Location not found: Unknown"

    database.close()


def test_save_weather(tmp_path):
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
        85.5,
        0.2,
        72.0,
    )

    database.commit()

    database.cursor.execute(
        """
        SELECT timestamp, temperature, precipitation, humidity
        FROM weather
        WHERE location_id = ?
        """,
        (location_id,),
    )

    result = database.cursor.fetchone()

    assert result == (
        "2026-10-05T12:00",
        85.5,
        0.2,
        72.0,
    )

    database.close()


def test_save_weather_updates_existing_record(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)

    database.create_tables()
    database.add_location(
        "Spring, TX",
        30.0799,
        -95.4172,
    )

    location_id = database.get_location_id("Spring, TX")

    timestamp = "2026-10-05T12:00"

    database.save_weather(
        location_id,
        timestamp,
        85.5,
        0.2,
        72.0,
    )

    database.save_weather(
        location_id,
        timestamp,
        90.0,
        0.5,
        65.0,
    )

    database.commit()

    database.cursor.execute(
        """
        SELECT timestamp, temperature, precipitation, humidity
        FROM weather
        WHERE location_id = ?
        """,
        (location_id,),
    )

    result = database.cursor.fetchall()

    assert len(result) == 1

    assert result[0] == (
        timestamp,
        90.0,
        0.5,
        65.0,
    )

    database.close()


def test_get_watermark_returns_latest_timestamp(tmp_path):
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

    database.save_weather(
        location_id,
        "2026-10-05T12:00",
        85.0,
        0.2,
        65.0,
    )

    database.commit()

    watermark = database.get_watermark(location_id)

    assert watermark == "2026-10-05T12:00"

    database.close()


def test_get_watermark_returns_none_when_no_weather_exists(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)

    database.create_tables()
    database.add_location(
        "Spring, TX",
        30.0799,
        -95.4172,
    )

    location_id = database.get_location_id("Spring, TX")

    watermark = database.get_watermark(location_id)

    assert watermark is None

    database.close()


def test_close_closes_database_connection(tmp_path):
    database_path = tmp_path / "test.db"

    database = WeatherDatabase(database_path)

    database.create_tables()
    database.close()

    try:
        database.cursor.execute("SELECT 1")
        assert False
    except Exception:
        pass
