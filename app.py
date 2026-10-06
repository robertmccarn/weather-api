from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from open_meteo import OpenMeteoClient
from radar.mrms import MRMSClient
from services.alert_service import AlertService
from services.geocoding_service import GeocodingService
from services.weather_service import WeatherService
from services.routing_service import RoutingService
from services.route_weather_service import RouteWeatherService
from services.radar_service import RadarService
from services.route_radar_service import RouteRadarService


app = FastAPI(title="Weather API")

client = OpenMeteoClient()
weather_service = WeatherService(client)
geocoding_service = GeocodingService()
alert_service = AlertService()
routing_service = RoutingService()
route_weather_service = RouteWeatherService(routing_service, weather_service)
radar_service = RadarService(MRMSClient())
route_radar_service = RouteRadarService(routing_service, radar_service)


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/api/forecast")
def forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    try:
        data = weather_service.get_forecast(
            latitude=latitude,
            longitude=longitude,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve weather forecast.",
        ) from error

    hourly = data["hourly"]
    daily = data.get("daily", {})

    hourly_records = []
    for index, time_value in enumerate(hourly["time"]):
        hourly_records.append(
            {
                "time": time_value,
                "temperature": hourly["temperature_2m"][index],
                "apparent_temperature": hourly.get(
                    "apparent_temperature", [None] * len(hourly["time"])
                )[index],
                "precipitation": hourly["precipitation"][index],
                "precipitation_probability": hourly.get(
                    "precipitation_probability",
                    [None] * len(hourly["time"]),
                )[index],
                "humidity": hourly["relative_humidity_2m"][index],
                "weather_code": hourly.get(
                    "weather_code", [None] * len(hourly["time"])
                )[index],
                "wind_speed": hourly.get(
                    "wind_speed_10m", [None] * len(hourly["time"])
                )[index],
                "wind_direction": hourly.get(
                    "wind_direction_10m", [None] * len(hourly["time"])
                )[index],
            }
        )

    daily_records = []
    for index, time_value in enumerate(daily.get("time", [])):
        daily_records.append(
            {
                "date": time_value,
                "weather_code": daily["weather_code"][index],
                "temperature_max": daily["temperature_2m_max"][index],
                "temperature_min": daily["temperature_2m_min"][index],
                "apparent_temperature_max": daily["apparent_temperature_max"][index],
                "apparent_temperature_min": daily["apparent_temperature_min"][index],
                "uv_index_max": daily["uv_index_max"][index],
                "sunrise": daily["sunrise"][index],
                "sunset": daily["sunset"][index],
                "precipitation": daily["precipitation_sum"][index],
                "precipitation_probability": daily["precipitation_probability_max"][index],
                "wind_speed_max": daily["wind_speed_10m_max"][index],
                "wind_direction_max": daily["wind_direction_10m_dominant"][index],
            }
        )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": data.get("timezone"),
        "hourly": hourly_records,
        "daily": daily_records,
    }


@app.get("/api/route-weather")
def route_weather(
    origin_latitude: float = Query(..., ge=-90, le=90),
    origin_longitude: float = Query(..., ge=-180, le=180),
    destination_latitude: float = Query(..., ge=-90, le=90),
    destination_longitude: float = Query(..., ge=-180, le=180),
    departure: str | None = Query(
        default=None,
        description="ISO-8601 departure time. Defaults to now.",
    ),
    sample_count: int = Query(default=12, ge=2, le=24),
):
    try:
        departure_time = (
            datetime.fromisoformat(departure.replace("Z", "+00:00"))
            if departure
            else datetime.now()
        )
        return route_weather_service.get_route_weather(
            origin=(origin_latitude, origin_longitude),
            destination=(destination_latitude, destination_longitude),
            departure_time=departure_time,
            sample_count=sample_count,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to calculate route weather.",
        ) from error


@app.get("/api/radar/precipitation")
def radar_precipitation(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    product: str = Query(default="1hr"),
):
    try:
        observation = radar_service.get_point_precipitation(
            latitude,
            longitude,
            product,
        )
        return observation.to_dict()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve radar precipitation.",
        ) from error


@app.get("/api/radar/route")
def radar_route(
    origin_latitude: float = Query(..., ge=-90, le=90),
    origin_longitude: float = Query(..., ge=-180, le=180),
    destination_latitude: float = Query(..., ge=-90, le=90),
    destination_longitude: float = Query(..., ge=-180, le=180),
    product: str = Query(default="1hr"),
    sample_count: int = Query(default=12, ge=2, le=24),
):
    try:
        return route_radar_service.get_route_radar(
            origin=(origin_latitude, origin_longitude),
            destination=(destination_latitude, destination_longitude),
            sample_count=sample_count,
            product=product,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve route radar precipitation.",
        ) from error


@app.get("/api/geocode/search")
def search_locations(q: str = Query(..., min_length=2, max_length=100)):
    try:
        return geocoding_service.search(q)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to search for that location.",
        ) from error


@app.get("/api/geocode/reverse")
def reverse_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    try:
        return geocoding_service.reverse(latitude, longitude)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to identify that location.",
        ) from error


@app.get("/api/alerts")
def alerts(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    try:
        return alert_service.get_point_alerts(latitude, longitude)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve weather alerts.",
        ) from error
