from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WeatherPoint:
    latitude: float
    longitude: float
    timestamp: str
    temperature: float | None = None
    apparent_temperature: float | None = None
    precipitation: float | None = None
    precipitation_probability: float | None = None
    humidity: float | None = None
    weather_code: int | None = None
    wind_speed: float | None = None
    wind_direction: float | None = None

    @classmethod
    def from_hourly(
        cls,
        latitude: float,
        longitude: float,
        hourly: dict[str, list[Any]],
        index: int,
    ) -> "WeatherPoint":
        times = hourly["time"]

        def value(name: str):
            values = hourly.get(name)
            return values[index] if values is not None else None

        return cls(
            latitude=latitude,
            longitude=longitude,
            timestamp=times[index],
            temperature=value("temperature_2m"),
            apparent_temperature=value("apparent_temperature"),
            precipitation=value("precipitation"),
            precipitation_probability=value("precipitation_probability"),
            humidity=value("relative_humidity_2m"),
            weather_code=value("weather_code"),
            wind_speed=value("wind_speed_10m"),
            wind_direction=value("wind_direction_10m"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp,
            "temperature": self.temperature,
            "apparent_temperature": self.apparent_temperature,
            "precipitation": self.precipitation,
            "precipitation_probability": self.precipitation_probability,
            "humidity": self.humidity,
            "weather_code": self.weather_code,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
        }
