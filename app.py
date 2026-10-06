from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from open_meteo import OpenMeteoClient
from services.alert_service import AlertService
from services.geocoding_service import GeocodingService
from services.weather_service import WeatherService


app = FastAPI(title="Weather API")

client = OpenMeteoClient()
weather_service = WeatherService(client)
geocoding_service = GeocodingService()
alert_service = AlertService()


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
                "wind_direction": daily["wind_direction_10m_dominant"][index],
            }
        )

    return {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": data.get("timezone"),
        "hourly": hourly_records,
        "daily": daily_records,
    }


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
