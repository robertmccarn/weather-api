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
