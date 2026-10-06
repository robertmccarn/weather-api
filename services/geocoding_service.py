import threading
import time
from typing import Any

import requests


class GeocodingService:
    def __init__(
        self,
        base_url: str = "https://nominatim.openstreetmap.org",
        user_agent: str = "weather-api/1.0 (educational project)",
        min_request_interval: float = 1.0,
        cache_ttl_seconds: int = 3600,
    ):
        self.base_url = base_url.rstrip("/")
        self.headers = {"User-Agent": user_agent}
        self.min_request_interval = min_request_interval
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[tuple[str, tuple[tuple[str, Any], ...]], tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._last_request = 0.0

    def _get(self, path: str, params: dict[str, Any]):
        cache_key = (path, tuple(sorted(params.items())))
        now = time.monotonic()

        cached = self._cache.get(cache_key)
        if cached and now - cached[0] < self.cache_ttl_seconds:
            return cached[1]

        with self._lock:
            now = time.monotonic()
            cached = self._cache.get(cache_key)
            if cached and now - cached[0] < self.cache_ttl_seconds:
                return cached[1]

            elapsed = now - self._last_request
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)

            response = requests.get(
                f"{self.base_url}{path}",
                params=params,
                headers=self.headers,
                timeout=10,
            )
            self._last_request = time.monotonic()
            response.raise_for_status()

        data = response.json()
        self._cache[cache_key] = (time.monotonic(), data)
        return data

    def search(self, query: str):
        return self._get(
            "/search",
            {
                "q": query,
                "format": "jsonv2",
                "limit": 5,
                "addressdetails": 1,
            },
        )

    def reverse(self, latitude: float, longitude: float):
        return self._get(
            "/reverse",
            {
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "addressdetails": 1,
                "zoom": 10,
            },
        )
