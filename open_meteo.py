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
            "hourly": "temperature_2m,precipitation,relative_humidity_2m",
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
