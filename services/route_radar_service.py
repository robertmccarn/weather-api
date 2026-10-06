from typing import Any

from services.radar_service import RadarService
from services.routing_service import RoutingService, sample_route


class RouteRadarService:
    def __init__(
        self,
        routing_service: RoutingService,
        radar_service: RadarService,
    ):
        self.routing_service = routing_service
        self.radar_service = radar_service

    def get_route_radar(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        sample_count: int = 12,
        product: str = "1hr",
    ) -> dict[str, Any]:
        route = self.routing_service.get_route(origin, destination)
        samples = sample_route(route["geometry"], sample_count)

        coordinates = [
            (sample["latitude"], sample["longitude"])
            for sample in samples
        ]
        observations = self.radar_service.get_points_precipitation(
            coordinates,
            product,
        )

        points = []
        for sample, observation in zip(samples, observations):
            points.append(
                {
                    "latitude": sample["latitude"],
                    "longitude": sample["longitude"],
                    "distance_km": round(sample["distance_km"], 2),
                    "precipitation_inches": observation.precipitation_inches,
                    "observed_at": observation.observed_at,
                }
            )

        values = [
            observation.precipitation_inches
            for observation in observations
            if observation.precipitation_inches is not None
        ]
        wet_points = [
            value for value in values if value > 0
        ]

        return {
            "origin": {
                "latitude": origin[0],
                "longitude": origin[1],
            },
            "destination": {
                "latitude": destination[0],
                "longitude": destination[1],
            },
            "distance_km": round(route["distance_km"], 2),
            "duration_minutes": round(route["duration_minutes"], 1),
            "geometry": route["geometry"],
            "product": product,
            "summary": {
                "sample_count": len(points),
                "wet_points": len(wet_points),
                "max_precipitation_inches": (
                    max(values) if values else None
                ),
                "average_precipitation_inches": (
                    sum(values) / len(values) if values else None
                ),
            },
            "points": points,
        }
