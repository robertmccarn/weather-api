from weather_database import WeatherDatabase


def test_create_tables_includes_radar_tables(tmp_path):
    database = WeatherDatabase(tmp_path / "test.db")
    database.create_tables()

    database.cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    )

    tables = {row[0] for row in database.cursor.fetchall()}

    assert "radar_frames" in tables
    assert "radar_observations" in tables

    database.close()


def test_save_radar_observation_is_idempotent(tmp_path):
    database = WeatherDatabase(tmp_path / "test.db")
    database.create_tables()

    frame_id = database.save_radar_observation(
        30.0799,
        -95.4172,
        0.42,
        "1hr",
        "2026-10-06T18:00:00Z",
    )
    database.save_radar_observation(
        30.0799,
        -95.4172,
        0.55,
        "1hr",
        "2026-10-06T18:00:00Z",
    )
    database.commit()

    database.cursor.execute(
        """
        SELECT radar_frame_id, precipitation_inches
        FROM radar_observations
        """
    )

    rows = database.cursor.fetchall()

    assert rows == [(frame_id, 0.55)]

    database.cursor.execute("SELECT COUNT(*) FROM radar_frames")
    assert database.cursor.fetchone()[0] == 1

    database.close()
