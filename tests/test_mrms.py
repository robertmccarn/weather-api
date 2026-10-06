from unittest.mock import Mock, patch

import pytest

from radar.mrms import MRMSClient


def test_parse_observation():
    data = {
        "samples": [
            {
                "value": 0.42,
                "attributes": {
                    "StdTime": "2026-10-06T18:00:00Z",
                },
            }
        ]
    }

    observation = MRMSClient._parse_observation(
        data,
        30.0799,
        -95.4172,
        "1hr",
    )

    assert observation.precipitation_inches == 0.42
    assert observation.product == "1hr"
    assert observation.observed_at == "2026-10-06T18:00:00Z"


def test_parse_nodata():
    observation = MRMSClient._parse_observation(
        {"samples": [{"value": "NoData"}]},
        30.0799,
        -95.4172,
        "1hr",
    )

    assert observation.precipitation_inches is None


def test_invalid_product():
    with pytest.raises(ValueError, match="Unsupported MRMS product"):
        MRMSClient().get_precipitation(30.0, -95.0, "bad")


def test_no_samples():
    with pytest.raises(ValueError, match="no samples"):
        MRMSClient._parse_observation(
            {"samples": []},
            30.0,
            -95.0,
            "1hr",
        )


@patch("radar.mrms.requests.get")
def test_get_precipitation_declares_wgs84_geometry(mock_get):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "samples": [
            {
                "value": 0.1,
                "attributes": {
                    "StdTime": "2026-10-06T18:00:00Z",
                },
            }
        ]
    }
    mock_get.return_value = response

    observation = MRMSClient().get_precipitation(
        30.0799,
        -95.4172,
    )

    params = mock_get.call_args.kwargs["params"]

    assert '"spatialReference":{"wkid":4326}' in params["geometry"]
    assert observation.precipitation_inches == 0.1
