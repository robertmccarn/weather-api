from open_meteo import OpenMeteoClient
from weather_database import WeatherDatabase
from weather_ingestion import WeatherIngestion

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
    {
        "name": "Dallas, TX",
        "latitude": 32.7767,
        "longitude": -96.7970,
    },
]


database = WeatherDatabase("weather.db")
client = OpenMeteoClient()


database.create_tables()

ingestion = WeatherIngestion(
    database,
    client,
    locations,
)

ingestion.run()

database.close()
