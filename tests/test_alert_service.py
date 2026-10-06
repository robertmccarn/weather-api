from unittest.mock import MagicMock, patch

from services.alert_service import AlertService


@patch("services.alert_service.requests.get")
def test_get_point_alerts_serializes_active_alerts(mock_get):
    response = MagicMock()
    response.json.return_value = {
        "features": [
            {
                "id": "alert-1",
                "properties": {
                    "event": "Heat Advisory",
                    "severity": "Moderate",
                    "urgency": "Expected",
                    "headline": "Heat advisory",
                    "description": "Take precautions.",
                    "expires": "2026-10-06T20:00:00Z",
                    "areaDesc": "Harris County",
                },
            }
        ]
    }
    mock_get.return_value = response

    service = AlertService(cache_ttl_seconds=60)
    alerts = service.get_point_alerts(29.7604, -95.3698)

    assert alerts == [
        {
            "id": "alert-1",
            "event": "Heat Advisory",
            "severity": "Moderate",
            "urgency": "Expected",
            "headline": "Heat advisory",
            "description": "Take precautions.",
            "expires": "2026-10-06T20:00:00Z",
            "area": "Harris County",
        }
    ]


@patch("services.alert_service.requests.get")
def test_get_point_alerts_uses_cache(mock_get):
    response = MagicMock()
    response.json.return_value = {"features": []}
    mock_get.return_value = response

    service = AlertService(cache_ttl_seconds=60)
    service.get_point_alerts(30, -95)
    service.get_point_alerts(30, -95)

    assert mock_get.call_count == 1
