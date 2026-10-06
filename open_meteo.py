import logging
import time

import requests

from config import API_URL


logger = logging.getLogger(__name__)


class OpenMeteoClient:
    API_URL = API_URL
    MAX_RETRIES = 3
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def get_forecast(self, latitude, longitude):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": (
                "temperature_2m,apparent_temperature,precipitation,"
                "relative_humidity_2m,weather_code,wind_speed_10m,"
                "wind_direction_10m"
            ),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "apparent_temperature_max,apparent_temperature_min,"
                "uv_index_max,sunrise,sunset,precipitation_sum,"
                "precipitation_probability_max,wind_speed_10m_max,"
                "wind_direction_10m_dominant"
            ),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(
                    self.API_URL,
                    params=params,
                    timeout=10,
                )

                if response.status_code in self.RETRYABLE_STATUS_CODES:
                    if attempt == self.MAX_RETRIES - 1:
                        response.raise_for_status()

                    wait_time = 2**attempt

                    logger.warning(
                        "Request failed with HTTP %s. "
                        "Retrying in %s seconds...",
                        response.status_code,
                        wait_time,
                    )

                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                data = response.json()

                self.validate_response(data)

                return data

            except requests.exceptions.Timeout:
                if attempt == self.MAX_RETRIES - 1:
                    raise

                wait_time = 2**attempt

                logger.warning(
                    "Request timed out. Retrying in %s seconds...",
                    wait_time,
                )

                time.sleep(wait_time)

            except requests.exceptions.ConnectionError:
                if attempt == self.MAX_RETRIES - 1:
                    raise

                wait_time = 2**attempt

                logger.warning(
                    "Connection failed. Retrying in %s seconds...",
                    wait_time,
                )

                time.sleep(wait_time)

    def validate_response(self, data):
        if "hourly" not in data:
            raise ValueError("API response is missing 'hourly'")

        required_fields = [
            "time",
            "temperature_2m",
            "precipitation",
            "relative_humidity_2m",
        ]

        for field in required_fields:
            if field not in data["hourly"]:
                raise ValueError(
                    f"API response is missing hourly field: {field}"
                )

        field_lengths = {
            field: len(data["hourly"][field])
            for field in required_fields
        }

        if len(set(field_lengths.values())) != 1:
            raise ValueError(
                "Hourly fields must contain the same number of records: "
                f"{field_lengths}"
            )
