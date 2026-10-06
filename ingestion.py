import logging

from config import LOCATIONS
from open_meteo import OpenMeteoClient
from weather_database import WeatherDatabase
from weather_ingestion import WeatherIngestion


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


database = WeatherDatabase("weather.db")
client = OpenMeteoClient()


database.create_tables()

ingestion = WeatherIngestion(
    database,
    client,
    LOCATIONS,
)

ingestion.run()

database.close()
