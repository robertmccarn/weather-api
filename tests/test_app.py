from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_forecast_returns_hourly_data():
    mock_data = {
        "hourly": {
            "time": ["2026-10-06T10:00", "2026-10-06T11:00"],
            "temperature_2m": [80.0, 82.0],
            "apparent_temperature": [81.0, 83.0],
            "precipitation": [0.0, 0.1],
            "precipitation_probability": [0, 20],
            "relative_humidity_2m": [70.0, 68.0],
            "weather_code": [0, 1],
            "wind_speed_10m": [5.0, 6.0],
            "wind_direction_10m": [180.0, 200.0],
        },
        "daily": {
            "time": ["2026-10-06"],
            "weather_code": [0],
            "temperature_2m_max": [88.0],
            "temperature_2m_min": [70.0],
            "apparent_temperature_max": [90.0],
            "apparent_temperature_min": [71.0],
            "uv_index_max": [7.0],
            "sunrise": ["2026-10-06T07:20"],
            "sunset": ["2026-10-06T19:00"],
            "precipitation_sum": [0.0],
            "precipitation_probability_max": [5],
            "wind_speed_10m_max": [12.0],
            "wind_direction_10m_dominant": [170.0],
        },
        "timezone": "America/Chicago",
    }

    with patch("app.client.get_forecast", return_value=mock_data):
        response = client.get(
            "/api/forecast?latitude=30.0799&longitude=-95.4172"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["latitude"] == 30.0799
    assert body["longitude"] == -95.4172
    assert body["timezone"] == "America/Chicago"
    assert body["hourly"][0]["temperature"] == 80.0
    assert body["hourly"][0]["apparent_temperature"] == 81.0
    assert body["hourly"][1]["humidity"] == 68.0
    assert body["hourly"][1]["precipitation_probability"] == 20
    assert body["daily"][0]["temperature_max"] == 88.0
    assert body["daily"][0]["precipitation_probability"] == 5


def test_forecast_rejects_invalid_coordinates():
    response = client.get(
        "/api/forecast?latitude=100&longitude=-95"
    )

    assert response.status_code == 422


def test_forecast_returns_bad_gateway_when_weather_service_fails():
    with patch(
        "app.client.get_forecast",
        side_effect=RuntimeError("API failure"),
    ):
        response = client.get(
            "/api/forecast?latitude=30&longitude=-95"
        )

    assert response.status_code == 502


def test_alerts_returns_point_alerts():
    mock_data = {
        "features": [
            {
                "id": "alert-1",
                "properties": {
                    "event": "Heat Advisory",
                    "severity": "Moderate",
                    "urgency": "Expected",
                    "headline": "Heat advisory in effect",
                    "description": "Take precautions.",
                    "expires": "2026-10-06T20:00:00Z",
                    "areaDesc": "Harris County",
                }
            }
        ]
    }

    with patch("app.alert_service.get_point_alerts", return_value=[
        {
            "id": "alert-1",
            "event": "Heat Advisory",
            "severity": "Moderate",
            "urgency": "Expected",
            "headline": "Heat advisory in effect",
            "description": "Take precautions.",
            "expires": "2026-10-06T20:00:00Z",
            "area": "Harris County",
        }
    ]):
        response = client.get(
            "/api/alerts?latitude=29.7604&longitude=-95.3698"
        )

    assert response.status_code == 200
    assert response.json()[0]["event"] == "Heat Advisory"


def test_route_weather_endpoint():
    mock_route = {
        "origin": {"latitude": 30.0, "longitude": -95.0},
        "destination": {"latitude": 31.0, "longitude": -94.0},
        "distance_km": 120.0,
        "duration_minutes": 120.0,
        "geometry": [
            {"latitude": 30.0, "longitude": -95.0},
            {"latitude": 31.0, "longitude": -94.0},
        ],
        "points": [
            {
                "latitude": 30.0,
                "longitude": -95.0,
                "distance_km": 0.0,
                "eta": "2026-10-06T10:00:00",
                "weather": {"temperature": 80.0},
            }
        ],
    }

    with patch("app.route_weather_service.get_route_weather", return_value=mock_route):
        response = client.get(
            "/api/route-weather"
            "?origin_latitude=30&origin_longitude=-95"
            "&destination_latitude=31&destination_longitude=-94"
            "&departure=2026-10-06T10:00:00"
        )

    assert response.status_code == 200
    assert response.json()["distance_km"] == 120.0
    assert response.json()["points"][0]["weather"]["temperature"] == 80.0


def test_route_weather_rejects_invalid_coordinates():
    response = client.get(
        "/api/route-weather"
        "?origin_latitude=100&origin_longitude=-95"
        "&destination_latitude=31&destination_longitude=-94"
    )

    assert response.status_code == 422
