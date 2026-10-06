from datetime import datetime
from unittest.mock import Mock

from services.route_weather_service import RouteWeatherService
from spatial.models import WeatherPoint


def test_route_weather_matches_each_sample_to_nearest_forecast():
    routing = Mock()
    weather = Mock()

    routing.get_route.return_value = {
        "distance_km": 120,
        "duration_minutes": 120,
        "geometry": [
            {"latitude": 30.0, "longitude": -95.0},
            {"latitude": 31.0, "longitude": -94.0},
        ],
    }

    weather.get_weather_points.return_value = [
        WeatherPoint(
            latitude=30.0,
            longitude=-95.0,
            timestamp="2026-10-06T10:00:00",
            temperature=80,
        ),
        WeatherPoint(
            latitude=30.5,
            longitude=-94.5,
            timestamp="2026-10-06T11:00:00",
            temperature=82,
        ),
        WeatherPoint(
            latitude=31.0,
            longitude=-94.0,
            timestamp="2026-10-06T12:00:00",
            temperature=85,
        ),
    ]

    service = RouteWeatherService(routing, weather)
    result = service.get_route_weather(
        (30.0, -95.0),
        (31.0, -94.0),
        datetime(2026, 10, 6, 10),
        sample_count=3,
    )

    assert len(result["points"]) == 3
    assert result["points"][0]["weather"]["temperature"] == 80
    assert result["points"][2]["weather"]["temperature"] == 85
