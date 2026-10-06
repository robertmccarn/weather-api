import sqlite3


class WeatherDatabase:
    def __init__(self, database_path):
        self.connection = sqlite3.connect(database_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.connection.cursor()

    def _deduplicate_locations(self):
        self.cursor.execute(
            """
            SELECT name, MIN(location_id)
            FROM locations
            GROUP BY name
            HAVING COUNT(*) > 1
            """
        )

        duplicates = self.cursor.fetchall()

        for name, canonical_id in duplicates:
            self.cursor.execute(
                """
                SELECT location_id
                FROM locations
                WHERE name = ?
                  AND location_id != ?
                """,
                (name, canonical_id),
            )

            duplicate_ids = [row[0] for row in self.cursor.fetchall()]

            for duplicate_id in duplicate_ids:
                self.cursor.execute(
                    """
                    DELETE FROM weather
                    WHERE location_id = ?
                      AND EXISTS (
                          SELECT 1
                          FROM weather AS canonical_weather
                          WHERE canonical_weather.location_id = ?
                            AND canonical_weather.timestamp = weather.timestamp
                      )
                    """,
                    (duplicate_id, canonical_id),
                )

                self.cursor.execute(
                    """
                    UPDATE weather
                    SET location_id = ?
                    WHERE location_id = ?
                    """,
                    (canonical_id, duplicate_id),
                )

                self.cursor.execute(
                    """
                    DELETE FROM locations
                    WHERE location_id = ?
                    """,
                    (duplicate_id,),
                )

    def create_tables(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS weather (
                weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                temperature REAL,
                precipitation REAL,
                humidity REAL,
                FOREIGN KEY (location_id)
                    REFERENCES locations(location_id),
                UNIQUE (location_id, timestamp)
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS radar_frames (
                radar_frame_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                source TEXT NOT NULL,
                UNIQUE (product, observed_at, source)
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS radar_observations (
                radar_observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                radar_frame_id INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                precipitation_inches REAL,
                FOREIGN KEY (radar_frame_id)
                    REFERENCES radar_frames(radar_frame_id),
                UNIQUE (
                    radar_frame_id,
                    latitude,
                    longitude
                )
            )
            """
        )

        self._deduplicate_locations()

        self.cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_locations_name
            ON locations(name)
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_weather_location_timestamp
            ON weather(location_id, timestamp)
            """
        )

        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_radar_observations_frame
            ON radar_observations(radar_frame_id)
            """
        )

        self.commit()

    def add_location(self, name, latitude, longitude):
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO locations (
                name,
                latitude,
                longitude
            )
            VALUES (?, ?, ?)
            """,
            (name, latitude, longitude),
        )

        self.commit()

    def get_location_id(self, name):
        self.cursor.execute(
            """
            SELECT location_id
            FROM locations
            WHERE name = ?
            """,
            (name,),
        )

        result = self.cursor.fetchone()

        if result is None:
            raise ValueError(f"Location not found: {name}")

        return result[0]

    def get_watermark(self, location_id):
        self.cursor.execute(
            """
            SELECT MAX(timestamp)
            FROM weather
            WHERE location_id = ?
            """,
            (location_id,),
        )

        result = self.cursor.fetchone()

        return result[0]

    def save_weather(
        self,
        location_id,
        timestamp,
        temperature,
        precipitation,
        humidity,
    ):
        self.cursor.execute(
            """
            INSERT INTO weather (
                location_id,
                timestamp,
                temperature,
                precipitation,
                humidity
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(location_id, timestamp)
            DO UPDATE SET
                temperature = excluded.temperature,
                precipitation = excluded.precipitation,
                humidity = excluded.humidity
            """,
            (
                location_id,
                timestamp,
                temperature,
                precipitation,
                humidity,
            ),
        )

    def save_radar_observation(
        self,
        latitude,
        longitude,
        precipitation_inches,
        product,
        observed_at,
        source="NOAA MRMS",
    ):
        self.cursor.execute(
            """
            INSERT INTO radar_frames (
                product,
                observed_at,
                source
            )
            VALUES (?, ?, ?)
            ON CONFLICT(product, observed_at, source)
            DO NOTHING
            """,
            (product, observed_at, source),
        )

        self.cursor.execute(
            """
            SELECT radar_frame_id
            FROM radar_frames
            WHERE product = ?
              AND observed_at = ?
              AND source = ?
            """,
            (product, observed_at, source),
        )

        frame = self.cursor.fetchone()
        if frame is None:
            raise ValueError("Unable to create or retrieve radar frame.")

        radar_frame_id = frame[0]

        self.cursor.execute(
            """
            INSERT INTO radar_observations (
                radar_frame_id,
                latitude,
                longitude,
                precipitation_inches
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(
                radar_frame_id,
                latitude,
                longitude
            )
            DO UPDATE SET
                precipitation_inches = excluded.precipitation_inches
            """,
            (
                radar_frame_id,
                latitude,
                longitude,
                precipitation_inches,
            ),
        )

        return radar_frame_id

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()
