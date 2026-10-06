import sqlite3


class WeatherDatabase:
    def __init__(self, database_path):
        self.connection = sqlite3.connect(database_path)
        self.cursor = self.connection.cursor()

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

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()
