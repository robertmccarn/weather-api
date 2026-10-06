from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app import app
from services.nws_observation_service import CurrentObservation, NWSObservationService


client = TestClient(app)


def test_nws_observation_service_converts_units():
    session = Mock()

    points_response = Mock()
    points_response.raise_for_status.return_value = None
    points_response.json.return_value = {
        "properties": {
            "observationStations": "https://api.weather.gov/gridpoints/HGX/1,1/stations"
        }
    }

    stations_response = Mock()
    stations_response.raise_for_status.return_value = None
    stations_response.json.return_value = {
        "features": [
            {
                "properties": {
                    "stationIdentifier": "KIAH",
                    "name": "Houston Intercontinental Airport",
                }
            }
        ]
    }

    observation_response = Mock()
    observation_response.raise_for_status.return_value = None
    observation_response.json.return_value = {
        "properties": {
            "timestamp": "2026-10-06T18:00:00+00:00",
            "temperature": {"value": 25},
            "heatIndex": {"value": 26},
            "relativeHumidity": {"value": 50},
            "windSpeed": {"value": 5},
            "windDirection": {"value": 180},
            "precipitationLastHour": {"value": 2.54},
            "textDescription": "Clear",
        }
    }

    session.get.side_effect = [
        points_response,
        stations_response,
        observation_response,
    ]

    service = NWSObservationService(session=session)
    result = service.get_observation(29.76, -95.36)

    assert result.station_id == "KIAH"
    assert round(result.temperature_f, 2) == 77.0
    assert round(result.apparent_temperature_f, 2) == 78.8
    assert round(result.wind_speed_mph, 2) == 11.18
    assert result.precipitation_last_hour_inches == 0.1
    assert result.text_description == "Clear"


def test_observations_endpoint():
    observation = CurrentObservation(
        station_id="KIAH",
        station_name="Houston Intercontinental Airport",
        timestamp="2026-10-06T18:00:00+00:00",
        temperature_f=77.0,
        apparent_temperature_f=78.8,
        relative_humidity=50.0,
        wind_speed_mph=11.18,
        wind_direction_deg=180.0,
        precipitation_last_hour_inches=0.1,
        text_description="Clear",
    )

    with patch(
        "app.nws_observation_service.get_observation",
        return_value=observation,
    ):
        response = client.get(
            "/api/observations?latitude=29.76&longitude=-95.36"
        )

    assert response.status_code == 200
    assert response.json() == observation.to_dict()


def test_observations_endpoint_returns_404_when_no_station():
    with patch(
        "app.nws_observation_service.get_observation",
        side_effect=ValueError("No NWS observation station is available nearby."),
    ):
        response = client.get(
            "/api/observations?latitude=29.76&longitude=-95.36"
        )

    assert response.status_code == 404
