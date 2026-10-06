import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

from spatial.coordinates import validate_coordinate


@dataclass(frozen=True)
class CurrentObservation:
    station_id: str
    station_name: str
    timestamp: str
    temperature_f: float | None
    apparent_temperature_f: float | None
    relative_humidity: float | None
    wind_speed_mph: float | None
    wind_direction_deg: float | None
    precipitation_last_hour_inches: float | None
    text_description: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "timestamp": self.timestamp,
            "temperature_f": self.temperature_f,
            "apparent_temperature_f": self.apparent_temperature_f,
            "relative_humidity": self.relative_humidity,
            "wind_speed_mph": self.wind_speed_mph,
            "wind_direction_deg": self.wind_direction_deg,
            "precipitation_last_hour_inches": self.precipitation_last_hour_inches,
            "text_description": self.text_description,
        }


class NWSObservationService:
    BASE_URL = "https://api.weather.gov"

    def __init__(
        self,
        timeout: int = 10,
        cache_seconds: int = 300,
        session: requests.Session | None = None,
    ):
        self.timeout = timeout
        self.cache_seconds = cache_seconds
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": os.getenv(
                    "NWS_USER_AGENT",
                    "weather-api/1.0 (https://github.com/robertmccarn/weather-api)",
                ),
                "Accept": "application/geo+json, application/json",
            }
        )
        self._station_cache: dict[
            tuple[float, float],
            tuple[float, str],
        ] = {}

    def get_observation(
        self,
        latitude: float,
        longitude: float,
    ) -> CurrentObservation:
        validate_coordinate(latitude, longitude)

        station_id, station_url = self._get_nearest_station(
            latitude,
            longitude,
        )

        station_payload = self._get_json(station_url)
        station_name = station_payload.get("properties", {}).get(
            "name",
            station_id,
        )

        latest_url = f"{self.BASE_URL}/stations/{station_id}/observations/latest"
        payload = self._get_json(latest_url)
        properties = payload.get("properties", {})

        return CurrentObservation(
            station_id=station_id,
            station_name=station_name,
            timestamp=properties.get("timestamp"),
            temperature_f=self._c_to_f(properties.get("temperature")),
            apparent_temperature_f=self._c_to_f(
                properties.get("heatIndex")
                or properties.get("windChill")
            ),
            relative_humidity=self._quantity(
                properties.get("relativeHumidity"),
            ),
            wind_speed_mph=self._meters_per_second_to_mph(
                properties.get("windSpeed"),
            ),
            wind_direction_deg=self._quantity(
                properties.get("windDirection"),
            ),
            precipitation_last_hour_inches=self._mm_to_inches(
                properties.get("precipitationLastHour"),
            ),
            text_description=properties.get("textDescription"),
        )

    def _get_nearest_station(
        self,
        latitude: float,
        longitude: float,
    ) -> tuple[str, str]:
        key = (round(latitude, 3), round(longitude, 3))
        cached = self._station_cache.get(key)
        if cached and (time.monotonic() - cached[0]) < self.cache_seconds:
            station_url = cached[1]
            return station_url.rsplit("/", 1)[-1], station_url

        points_url = f"{self.BASE_URL}/points/{latitude:.4f},{longitude:.4f}"
        payload = self._get_json(points_url)
        station_url = payload.get("properties", {}).get(
            "observationStations",
        )
        if not station_url:
            raise ValueError("NWS did not provide observation stations.")

        station_payload = self._get_json(station_url)
        features = station_payload.get("features", [])
        if not features:
            raise ValueError("No NWS observation station is available nearby.")

        station = features[0]
        station_id = (
            station.get("properties", {}).get("stationIdentifier")
            or station.get("id", "").rsplit("/", 1)[-1]
        )
        if not station_id:
            raise ValueError("NWS observation station did not provide an ID.")

        self._station_cache[key] = (time.monotonic(), f"{self.BASE_URL}/stations/{station_id}")
        return station_id, self._station_cache[key][1]

    def _get_json(self, url: str) -> dict[str, Any]:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("NWS returned an unexpected response.")
        return payload

    @staticmethod
    def _quantity(value: Any) -> float | None:
        if not isinstance(value, dict):
            return None
        raw = value.get("value")
        return float(raw) if raw is not None else None

    @staticmethod
    def _c_to_f(value: Any) -> float | None:
        celsius = NWSObservationService._quantity(value)
        return None if celsius is None else celsius * 9 / 5 + 32

    @staticmethod
    def _meters_per_second_to_mph(value: Any) -> float | None:
        meters_per_second = NWSObservationService._quantity(value)
        return (
            None
            if meters_per_second is None
            else meters_per_second * 2.2369362920544
        )

    @staticmethod
    def _mm_to_inches(value: Any) -> float | None:
        millimeters = NWSObservationService._quantity(value)
        return None if millimeters is None else millimeters / 25.4
