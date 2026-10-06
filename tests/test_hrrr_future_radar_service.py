from datetime import datetime, timezone
from unittest.mock import Mock, patch

from services.hrrr_future_radar_service import HRRRFutureRadarService


def test_get_next_six_hours_builds_future_frames():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "model_init_utc": "2026-10-06T00:00:00Z"
    }

    with patch(
        "services.hrrr_future_radar_service.requests.get",
        return_value=response,
    ), patch(
        "services.hrrr_future_radar_service.datetime"
    ) as datetime_mock:
        datetime_mock.fromtimestamp.side_effect = datetime.fromtimestamp
        datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
        datetime_mock.now.return_value = datetime(
            2026,
            10,
            6,
            0,
            0,
            tzinfo=timezone.utc,
        )
        result = HRRRFutureRadarService().get_next_six_hours()

    assert result["model"] == "HRRR"
    assert len(result["frames"]) == 24
    assert result["frames"][0]["forecast_minute"] > 0
    assert result["frames"][-1]["forecast_minute"] == result["frames"][0]["forecast_minute"] + 345


def test_get_model_init_accepts_z_timestamp():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "model_init_utc": "2026-10-06T00:00:00Z"
    }

    with patch(
        "services.hrrr_future_radar_service.requests.get",
        return_value=response,
    ):
        result = HRRRFutureRadarService().get_model_init()

    assert result == datetime(2026, 10, 6, tzinfo=timezone.utc)
