from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app
from radar.mrms import RadarObservation


client = TestClient(app)


def test_radar_precipitation_endpoint():
    observation = RadarObservation(
        latitude=30.0799,
        longitude=-95.4172,
        precipitation_inches=0.42,
        product="1hr",
        observed_at="2026-10-06T18:00:00Z",
    )

    with patch(
        "app.radar_service.get_point_precipitation",
        return_value=observation,
    ):
        response = client.get(
            "/api/radar/precipitation"
            "?latitude=30.0799&longitude=-95.4172&product=1hr"
        )

    assert response.status_code == 200
    assert response.json() == observation.to_dict()


def test_radar_precipitation_rejects_invalid_product():
    response = client.get(
        "/api/radar/precipitation"
        "?latitude=30.0799&longitude=-95.4172&product=bad"
    )

    assert response.status_code == 400


def test_route_radar_endpoint():
    route_radar = {
        "origin": {"latitude": 30.0, "longitude": -95.0},
        "destination": {"latitude": 31.0, "longitude": -94.0},
        "distance_km": 100.0,
        "duration_minutes": 120.0,
        "geometry": [
            {"latitude": 30.0, "longitude": -95.0},
            {"latitude": 31.0, "longitude": -94.0},
        ],
        "product": "1hr",
        "summary": {
            "sample_count": 2,
            "wet_points": 1,
            "max_precipitation_inches": 0.12,
            "average_precipitation_inches": 0.12,
        },
        "points": [
            {
                "latitude": 30.0,
                "longitude": -95.0,
                "distance_km": 0.0,
                "precipitation_inches": 0.0,
                "observed_at": "2026-10-06T18:00:00Z",
            },
            {
                "latitude": 31.0,
                "longitude": -94.0,
                "distance_km": 100.0,
                "precipitation_inches": 0.12,
                "observed_at": "2026-10-06T18:00:00Z",
            },
        ],
    }

    with patch(
        "app.route_radar_service.get_route_radar",
        return_value=route_radar,
    ):
        response = client.get(
            "/api/radar/route"
            "?origin_latitude=30&origin_longitude=-95"
            "&destination_latitude=31&destination_longitude=-94"
            "&sample_count=2"
        )

    assert response.status_code == 200
    assert response.json() == route_radar


def test_route_radar_rejects_invalid_product():
    response = client.get(
        "/api/radar/route"
        "?origin_latitude=30&origin_longitude=-95"
        "&destination_latitude=31&destination_longitude=-94"
        "&product=bad"
    )

    assert response.status_code == 400
