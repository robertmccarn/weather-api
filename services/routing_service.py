from typing import Any

import requests

from spatial.coordinates import haversine_distance_km, validate_coordinate


class RoutingService:
    """Route driving requests through the public OSRM routing service."""

    BASE_URL = "https://router.project-osrm.org/route/v1/driving"
    TIMEOUT_SECONDS = 10

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or self.BASE_URL

    def get_route(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ) -> dict[str, Any]:
        origin_lat, origin_lon = origin
        destination_lat, destination_lon = destination
        validate_coordinate(origin_lat, origin_lon)
        validate_coordinate(destination_lat, destination_lon)

        url = (
            f"{self.base_url}/"
            f"{origin_lon},{origin_lat};{destination_lon},{destination_lat}"
        )
        response = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson"},
            timeout=self.TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            raise ValueError("Routing service returned no route.")

        route = data["routes"][0]
        geometry = route.get("geometry", {}).get("coordinates", [])
        if len(geometry) < 2:
            raise ValueError("Routing service returned insufficient route geometry.")

        return {
            "distance_km": route["distance"] / 1000,
            "duration_minutes": route["duration"] / 60,
            "geometry": [
                {"latitude": latitude, "longitude": longitude}
                for longitude, latitude in geometry
            ],
        }


def sample_route(
    geometry: list[dict[str, float]],
    count: int = 12,
) -> list[dict[str, float]]:
    if len(geometry) < 2:
        raise ValueError("Route geometry must contain at least two points.")
    if count < 2:
        raise ValueError("count must be at least 2.")

    segment_distances = []
    total_distance = 0.0

    for start, end in zip(geometry, geometry[1:]):
        distance = haversine_distance_km(
            start["latitude"],
            start["longitude"],
            end["latitude"],
            end["longitude"],
        )
        segment_distances.append(distance)
        total_distance += distance

    if total_distance == 0:
        return [
            {
                "latitude": geometry[0]["latitude"],
                "longitude": geometry[0]["longitude"],
                "distance_km": 0.0,
            }
        ]

    targets = [
        total_distance * index / (count - 1)
        for index in range(count)
    ]
    samples = []
    segment_index = 0
    segment_start_distance = 0.0

    for target in targets:
        while (
            segment_index < len(segment_distances) - 1
            and target > segment_start_distance + segment_distances[segment_index]
        ):
            segment_start_distance += segment_distances[segment_index]
            segment_index += 1

        segment_length = segment_distances[segment_index]
        fraction = (
            0.0
            if segment_length == 0
            else (target - segment_start_distance) / segment_length
        )
        start = geometry[segment_index]
        end = geometry[segment_index + 1]

        samples.append(
            {
                "latitude": start["latitude"]
                + (end["latitude"] - start["latitude"]) * fraction,
                "longitude": start["longitude"]
                + (end["longitude"] - start["longitude"]) * fraction,
                "distance_km": target,
            }
        )

    return samples
