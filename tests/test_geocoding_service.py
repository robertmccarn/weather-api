from unittest.mock import MagicMock, patch

from services.geocoding_service import GeocodingService


@patch("services.geocoding_service.requests.get")
def test_search_returns_json_and_caches(mock_get):
    response = MagicMock()
    response.json.return_value = [{"display_name": "Spring, Texas"}]
    mock_get.return_value = response

    service = GeocodingService(min_request_interval=0, cache_ttl_seconds=60)

    first = service.search("Spring, TX")
    second = service.search("Spring, TX")

    assert first == second
    assert mock_get.call_count == 1
    response.raise_for_status.assert_called_once()


@patch("services.geocoding_service.requests.get")
def test_reverse_sends_coordinates(mock_get):
    response = MagicMock()
    response.json.return_value = {"display_name": "Spring, Texas"}
    mock_get.return_value = response

    service = GeocodingService(min_request_interval=0)
    result = service.reverse(30.0799, -95.4172)

    assert result["display_name"] == "Spring, Texas"
    assert mock_get.call_args.kwargs["params"]["lat"] == 30.0799
    assert mock_get.call_args.kwargs["params"]["lon"] == -95.4172
