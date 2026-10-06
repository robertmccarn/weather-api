from typing import Any

from open_meteo import OpenMeteoClient
from spatial.models import WeatherPoint


class WeatherService:
    def __init__(self, client: OpenMeteoClient):
        self.client = client

    def get_forecast(self, latitude: float, longitude: float) -> dict[str, Any]:
        return self.client.get_forecast(latitude, longitude)

    def get_weather_points(
        self,
        coordinates: list[tuple[float, float]],
    ) -> list[WeatherPoint]:
        return [
            point
            for series in self.get_weather_series(coordinates)
            for point in series
        ]

    def get_weather_series(
        self,
        coordinates: list[tuple[float, float]],
    ) -> list[list[WeatherPoint]]:
        if not coordinates:
            return []

        forecasts = self.client.get_forecast_batch(coordinates)
        series = []

        for (latitude, longitude), forecast in zip(coordinates, forecasts):
            hourly = forecast["hourly"]
            series.append(
                [
                    WeatherPoint.from_hourly(
                        latitude,
                        longitude,
                        hourly,
                        index,
                    )
                    for index in range(len(hourly["time"]))
                ]
            )

        return series
