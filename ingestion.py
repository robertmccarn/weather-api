import logging

from config import LOCATIONS
from open_meteo import OpenMeteoClient
from weather_database import WeatherDatabase
from weather_ingestion import WeatherIngestion


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def run_ingestion(
    database_path: str = "weather.db",
    locations=None,
):
    selected_locations = LOCATIONS if locations is None else locations

    database = WeatherDatabase(database_path)
    client = OpenMeteoClient()

    try:
        database.create_tables()

        ingestion = WeatherIngestion(
            database,
            client,
            selected_locations,
        )

        return ingestion.run()
    finally:
        database.close()


if __name__ == "__main__":
    run_ingestion()
