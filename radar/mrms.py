import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from spatial.coordinates import validate_coordinate


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RadarObservation:
    latitude: float
    longitude: float
    precipitation_inches: float | None
    product: str
    observed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "precipitation_inches": self.precipitation_inches,
            "product": self.product,
            "observed_at": self.observed_at,
        }


class MRMSClient:
    BASE_URL = (
        "https://mapservices.weather.noaa.gov/"
        "raster/rest/services/obs/mrms_qpe/ImageServer/getSamples"
    )
    PRODUCT_RULES = {
        "1hr": "rft_1hr",
        "3hr": "rft_3hr",
        "6hr": "rft_6hr",
        "12hr": "rft_12hr",
        "24hr": "rft_24hr",
        "48hr": "rft_48hr",
        "72hr": "rft_72hr",
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_precipitation(
        self,
        latitude: float,
        longitude: float,
        product: str = "1hr",
    ) -> RadarObservation:
        validate_coordinate(latitude, longitude)

        if product not in self.PRODUCT_RULES:
            raise ValueError(
                f"Unsupported MRMS product: {product}. "
                f"Choose one of {sorted(self.PRODUCT_RULES)}"
            )

        params = {
            "geometry": f'{{"x":{longitude},"y":{latitude}}}',
            "geometryType": "esriGeometryPoint",
            "geometrySR": "4326",
            "sampleCount": 1,
            "returnFirstValueOnly": "true",
            "interpolation": "RSP_NearestNeighbor",
            "format": "json",
            "renderingRule": (
                f'{{"rasterFunction":"{self.PRODUCT_RULES[product]}"}}'
            ),
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()
        return self._parse_observation(
            data,
            latitude,
            longitude,
            product,
        )

    @staticmethod
    def _parse_observation(
        data: dict[str, Any],
        latitude: float,
        longitude: float,
        product: str,
    ) -> RadarObservation:
        samples = data.get("samples", [])
        if not samples:
            raise ValueError("MRMS returned no samples for the requested point.")

        sample = samples[0]
        raw_value = sample.get("value")

        if raw_value in (None, "", "NoData"):
            precipitation = None
        else:
            precipitation = float(raw_value)

        observed_at = (
            sample.get("attributes", {}).get("StdTime")
            or sample.get("attributes", {}).get("time")
            or datetime.now(timezone.utc).isoformat()
        )

        return RadarObservation(
            latitude=latitude,
            longitude=longitude,
            precipitation_inches=precipitation,
            product=product,
            observed_at=observed_at,
        )
