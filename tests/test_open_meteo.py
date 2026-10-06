from unittest.mock import MagicMock, patch

import pytest
import requests

from open_meteo import OpenMeteoClient


def valid_response():
    return {
        "hourly": {
            "time": ["2026-10-06T10:00"],
            "temperature_2m": [80.0],
            "precipitation": [0.0],
            "relative_humidity_2m": [70.0],
        },
        "daily": {
            "time": ["2026-10-06"],
            "weather_code": [0],
            "temperature_2m_max": [88.0],
            "temperature_2m_min": [70.0],
            "precipitation_sum": [0.0],
        },
    }


def test_validate_response_accepts_valid_data():
    OpenMeteoClient().validate_response(valid_response())


def test_validate_response_rejects_non_object():
    with pytest.raises(ValueError, match="must be an object"):
        OpenMeteoClient().validate_response([])


def test_validate_response_rejects_missing_hourly():
    data = valid_response()
    del data["hourly"]

    with pytest.raises(ValueError, match="hourly"):
        OpenMeteoClient().validate_response(data)


def test_validate_response_rejects_missing_daily():
    data = valid_response()
    del data["daily"]

    with pytest.raises(ValueError, match="daily"):
        OpenMeteoClient().validate_response(data)


def test_validate_response_rejects_missing_field():
    data = valid_response()
    del data["hourly"]["temperature_2m"]

    with pytest.raises(ValueError, match="temperature_2m"):
        OpenMeteoClient().validate_response(data)


def test_validate_response_rejects_mismatched_field_lengths():
    data = valid_response()
    data["hourly"]["time"] = [
        "2026-10-06T10:00",
        "2026-10-06T11:00",
    ]

    with pytest.raises(ValueError, match="same number of records"):
        OpenMeteoClient().validate_response(data)


def test_validate_response_rejects_mismatched_daily_lengths():
    data = valid_response()
    data["daily"]["temperature_2m_max"] = [88.0, 89.0]

    with pytest.raises(ValueError, match="Daily fields"):
        OpenMeteoClient().validate_response(data)


@patch("open_meteo.time.sleep")
@patch("open_meteo.requests.get")
def test_get_forecast_retries_on_server_error(mock_get, mock_sleep):
    client = OpenMeteoClient()
    mock_response = mock_get.return_value
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception("Server error")

    with pytest.raises(Exception):
        client.get_forecast(30.0799, -95.4172)

    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0].args == (1,)
    assert mock_sleep.call_args_list[1].args == (2,)


@patch("open_meteo.time.sleep")
@patch("open_meteo.requests.get")
def test_get_forecast_succeeds_after_retry(mock_get, mock_sleep):
    client = OpenMeteoClient()
    failed_response = MagicMock()
    failed_response.status_code = 500
    successful_response = MagicMock()
    successful_response.status_code = 200
    successful_response.json.return_value = valid_response()
    mock_get.side_effect = [failed_response, failed_response, successful_response]

    result = client.get_forecast(30.0799, -95.4172)

    assert result == successful_response.json.return_value
    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2


@patch("open_meteo.time.sleep")
@patch("open_meteo.requests.get")
def test_get_forecast_retries_on_timeout(mock_get, mock_sleep):
    client = OpenMeteoClient()
    mock_get.side_effect = [
        requests.exceptions.Timeout("Request timed out"),
        requests.exceptions.Timeout("Request timed out"),
        requests.exceptions.Timeout("Request timed out"),
    ]

    with pytest.raises(requests.exceptions.Timeout):
        client.get_forecast(30.0799, -95.4172)

    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2


@patch("open_meteo.time.sleep")
@patch("open_meteo.requests.get")
def test_get_forecast_does_not_retry_on_bad_request(mock_get, mock_sleep):
    client = OpenMeteoClient()
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "400 Bad Request"
    )
    mock_get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        client.get_forecast(30.0799, -95.4172)

    assert mock_get.call_count == 1
    assert mock_sleep.call_count == 0


@patch("open_meteo.requests.get")
def test_get_forecast_batch_returns_one_forecast_per_coordinate(mock_get):
    client = OpenMeteoClient()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [valid_response(), valid_response()]
    mock_get.return_value = mock_response

    result = client.get_forecast_batch([
        (30.0799, -95.4172),
        (29.7604, -95.3698),
    ])

    assert len(result) == 2
    assert mock_get.call_count == 1


def test_get_forecast_batch_returns_empty_for_no_coordinates():
    assert OpenMeteoClient().get_forecast_batch([]) == []
