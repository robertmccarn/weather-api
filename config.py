import os

from dotenv import load_dotenv

load_dotenv()


API_URL = os.getenv(
    "OPEN_METEO_API_URL",
    "https://api.open-meteo.com/v1/forecast",
)


LOCATIONS = [
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
