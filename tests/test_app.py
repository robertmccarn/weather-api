from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_forecast_returns_hourly_data():
    mock_data = {
        "hourly": {
            "time": ["2026-10-06T10:00", "2026-10-06T11:00"],
            "temperature_2m": [80.0, 82.0],
            "precipitation": [0.0, 0.1],
            "relative_humidity_2m": [70.0, 68.0],
        }
    }

    with patch("app.client.get_forecast", return_value=mock_data):
        response = client.get("/api/forecast?latitude=30.0799&longitude=-95.4172")

    assert response.status_code == 200
    assert response.json()["hourly"][0]["temperature"] == 80.0
    assert response.json()["hourly"][1]["humidity"] == 68.0


def test_forecast_rejects_invalid_coordinates():
    response = client.get("/api/forecast?latitude=100&longitude=-95")
    assert response.status_code == 422


def test_forecast_returns_bad_gateway_when_weather_service_fails():
    with patch("app.client.get_forecast", side_effect=RuntimeError("API failure")):
        response = client.get("/api/forecast?latitude=30&longitude=-95")

    assert response.status_code == 502