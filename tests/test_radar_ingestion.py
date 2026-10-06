from unittest.mock import patch

from radar.mrms import RadarObservation
from radar_ingestion import run_radar_ingestion


def test_radar_ingestion_persists_observations(tmp_path):
    locations = [
        {
            "name": "Spring, TX",
            "latitude": 30.0799,
            "longitude": -95.4172,
        },
        {
            "name": "Houston, TX",
            "latitude": 29.7604,
            "longitude": -95.3698,
        },
    ]

    observations = [
        RadarObservation(
            30.0799,
            -95.4172,
            0.42,
            "1hr",
            "2026-10-06T18:00:00Z",
        ),
        RadarObservation(
            29.7604,
            -95.3698,
            0.15,
            "1hr",
            "2026-10-06T18:00:00Z",
        ),
    ]

    with patch(
        "radar_ingestion.MRMSClient.get_precipitation",
        side_effect=observations,
    ):
        summary = run_radar_ingestion(
            database_path=str(tmp_path / "test.db"),
            locations=locations,
        )

    assert summary == {
        "locations_processed": 2,
        "locations_failed": 0,
    }
