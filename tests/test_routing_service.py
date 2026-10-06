from unittest.mock import patch

import pytest

from services.routing_service import RoutingService, sample_route


def test_routing_service_returns_route():
    response = type(
        "Response",
        (),
        {
            "raise_for_status": lambda self: None,
            "json": lambda self: {
                "code": "Ok",
                "routes": [
                    {
                        "distance": 100000,
                        "duration": 7200,
                        "geometry": {
                            "coordinates": [
                                [-95.4, 30.1],
                                [-95.2, 30.2],
                            ]
                        },
                    }
                ],
            },
        },
    )()

    with patch("services.routing_service.requests.get", return_value=response):
        route = RoutingService().get_route((30.1, -95.4), (30.2, -95.2))

    assert route["distance_km"] == 100
    assert route["duration_minutes"] == 120
    assert route["geometry"][0] == {"latitude": 30.1, "longitude": -95.4}


def test_sample_route_uses_distance_along_geometry():
    geometry = [
        {"latitude": 30.0, "longitude": -95.0},
        {"latitude": 30.0, "longitude": -94.9},
        {"latitude": 30.1, "longitude": -94.9},
    ]

    samples = sample_route(geometry, 5)

    assert len(samples) == 5
    assert samples[0]["distance_km"] == 0
    assert samples[-1]["distance_km"] > samples[0]["distance_km"]
    assert samples[-1]["latitude"] == geometry[-1]["latitude"]
    assert samples[-1]["longitude"] == geometry[-1]["longitude"]


def test_sample_route_rejects_invalid_count():
    with pytest.raises(ValueError):
        sample_route(
            [{"latitude": 30, "longitude": -95}, {"latitude": 31, "longitude": -94}],
            1,
        )
