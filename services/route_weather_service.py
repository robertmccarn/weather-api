from datetime import datetime, timedelta
from typing import Any

from services.routing_service import RoutingService, sample_route
from services.weather_service import WeatherService


class RouteWeatherService:
    def __init__(
        self,
        routing_service: RoutingService,
        weather_service: WeatherService,
    ):
        self.routing_service = routing_service
        self.weather_service = weather_service

    def get_route_weather(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        departure_time: datetime,
        sample_count: int = 12,
    ) -> dict[str, Any]:
        route = self.routing_service.get_route(origin, destination)
        samples = sample_route(route["geometry"], sample_count)

        coordinates = [
            (sample["latitude"], sample["longitude"])
            for sample in samples
        ]
        forecasts = self.weather_service.get_weather_points(coordinates)

        route_start = departure_time
        duration = timedelta(minutes=route["duration_minutes"])

        points = []
        for sample, forecast_points in self._group_forecasts(
            samples,
            forecasts,
        ):
            eta = route_start + duration * (
                sample["distance_km"] / route["distance_km"]
                if route["distance_km"]
                else 0
            )
            weather = self._nearest_forecast(forecast_points, eta)
            points.append(
                {
                    "latitude": sample["latitude"],
                    "longitude": sample["longitude"],
                    "distance_km": round(sample["distance_km"], 2),
                    "eta": eta.isoformat(),
                    "weather": weather.to_dict() if weather else None,
                }
            )

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
            "points": points,
        }

    @staticmethod
    def _group_forecasts(samples, forecasts):
        grouped = []
        for index, sample in enumerate(samples):
            grouped.append((sample, forecasts[index:index + 1]))
        return grouped

    @staticmethod
    def _nearest_forecast(forecasts, target: datetime):
        if not forecasts:
            return None

        return min(
            forecasts,
            key=lambda point: abs(
                RouteWeatherService._parse_timestamp(point.timestamp) - target
            ),
        )

    @staticmethod
    def _parse_timestamp(timestamp: str) -> datetime:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
