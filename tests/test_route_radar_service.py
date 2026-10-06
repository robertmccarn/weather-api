from unittest.mock import Mock

from services.route_radar_service import RouteRadarService
from radar.mrms import RadarObservation


def test_route_radar_returns_precipitation_along_route():
    routing = Mock()
    radar = Mock()

    routing.get_route.return_value = {
        "distance_km": 100,
        "duration_minutes": 120,
        "geometry": [
            {"latitude": 30.0, "longitude": -95.0},
            {"latitude": 31.0, "longitude": -94.0},
        ],
    }

    radar.get_points_precipitation.return_value = [
        RadarObservation(30.0, -95.0, 0.0, "1hr", "2026-10-06T18:00:00Z"),
        RadarObservation(30.5, -94.5, 0.12, "1hr", "2026-10-06T18:00:00Z"),
        RadarObservation(31.0, -94.0, None, "1hr", "2026-10-06T18:00:00Z"),
    ]

    service = RouteRadarService(routing, radar)
    result = service.get_route_radar(
        (30.0, -95.0),
        (31.0, -94.0),
        sample_count=3,
    )

    assert len(result["points"]) == 3
    assert result["points"][1]["precipitation_inches"] == 0.12
    assert result["summary"]["wet_points"] == 1
    assert result["summary"]["max_precipitation_inches"] == 0.12
    assert result["summary"]["average_precipitation_inches"] == 0.06
    assert result["geometry"] == routing.get_route.return_value["geometry"]
