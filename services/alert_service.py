import threading
import time
from typing import Any

import requests


class AlertService:
    def __init__(
        self,
        base_url: str = "https://api.weather.gov",
        user_agent: str = "weather-api/1.0 (educational project)",
        cache_ttl_seconds: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/geo+json",
        }
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[tuple[float, float], tuple[float, list[dict[str, Any]]]] = {}
        self._lock = threading.Lock()

    def get_point_alerts(self, latitude: float, longitude: float):
        key = (round(latitude, 4), round(longitude, 4))
        now = time.monotonic()
        cached = self._cache.get(key)

        if cached and now - cached[0] < self.cache_ttl_seconds:
            return cached[1]

        with self._lock:
            now = time.monotonic()
            cached = self._cache.get(key)
            if cached and now - cached[0] < self.cache_ttl_seconds:
                return cached[1]

            response = requests.get(
                f"{self.base_url}/alerts/active",
                params={"point": f"{latitude},{longitude}"},
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()

        features = response.json().get("features", [])
        alerts = [
            self._serialize_feature(feature)
            for feature in features
        ]
        self._cache[key] = (time.monotonic(), alerts)
        return alerts

    @staticmethod
    def _serialize_feature(feature):
        properties = feature.get("properties", {})
        return {
            "id": feature.get("id"),
            "event": properties.get("event"),
            "severity": properties.get("severity"),
            "urgency": properties.get("urgency"),
            "headline": properties.get("headline"),
            "description": properties.get("description"),
            "expires": properties.get("expires"),
            "area": properties.get("areaDesc"),
        }
