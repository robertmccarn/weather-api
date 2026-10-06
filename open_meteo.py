import logging
import time

import requests

from config import API_URL


logger = logging.getLogger(__name__)


class OpenMeteoClient:
    API_URL = API_URL
    MAX_RETRIES = 3
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    HOURLY_FIELDS = (
        "temperature_2m,apparent_temperature,precipitation,"
        "precipitation_probability,relative_humidity_2m,weather_code,"
        "wind_speed_10m,wind_direction_10m"
    )

    DAILY_FIELDS = (
        "weather_code,temperature_2m_max,temperature_2m_min,"
        "apparent_temperature_max,apparent_temperature_min,"
        "uv_index_max,sunrise,sunset,precipitation_sum,"
        "precipitation_probability_max,wind_speed_10m_max,"
        "wind_direction_10m_dominant"
    )

    REQUIRED_HOURLY_FIELDS = (
        "time",
        "temperature_2m",
        "precipitation",
        "relative_humidity_2m",
    )

    REQUIRED_DAILY_FIELDS = (
        "time",
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
    )

    def _build_params(self, latitudes, longitudes):
        return {
            "latitude": ",".join(str(value) for value in latitudes),
            "longitude": ",".join(str(value) for value in longitudes),
            "hourly": self.HOURLY_FIELDS,
            "daily": self.DAILY_FIELDS,
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "auto",
        }

    def _request(self, params):
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
                        "Request failed with HTTP %s. Retrying in %s seconds...",
                        response.status_code,
                        wait_time,
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()
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

    def get_forecast(self, latitude, longitude):
        data = self._request(
            self._build_params([latitude], [longitude])
        )

        if isinstance(data, list):
            if len(data) != 1:
                raise ValueError("Expected one forecast in single-location response.")
            data = data[0]

        self.validate_response(data)
        return data

    def get_forecast_batch(self, coordinates):
        if not coordinates:
            return []

        latitudes = [latitude for latitude, _ in coordinates]
        longitudes = [longitude for _, longitude in coordinates]

        data = self._request(
            self._build_params(latitudes, longitudes)
        )

        forecasts = data if isinstance(data, list) else [data]

        if len(forecasts) != len(coordinates):
            raise ValueError(
                "Open-Meteo returned a different number of forecasts "
                f"than requested: expected {len(coordinates)}, got {len(forecasts)}"
            )

        for forecast in forecasts:
            self.validate_response(forecast)

        return forecasts

    @staticmethod
    def _validate_series(data: dict, section: str, required_fields: tuple[str, ...]):
        if section not in data:
            raise ValueError(f"API response is missing '{section}'")

        values = data[section]

        for field in required_fields:
            if field not in values:
                raise ValueError(
                    f"API response is missing {section} field: {field}"
                )

        field_lengths = {
            field: len(values[field])
            for field in required_fields
        }

        if len(set(field_lengths.values())) != 1:
            raise ValueError(
                f"{section.capitalize()} fields must contain the same number "
                f"of records: {field_lengths}"
            )

    def validate_response(self, data):
        if not isinstance(data, dict):
            raise ValueError("API response must be an object.")

        self._validate_series(
            data,
            "hourly",
            self.REQUIRED_HOURLY_FIELDS,
        )

        self._validate_series(
            data,
            "daily",
            self.REQUIRED_DAILY_FIELDS,
        )
