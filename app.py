from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from open_meteo import OpenMeteoClient


app = FastAPI(title="Weather API")
client = OpenMeteoClient()


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/api/forecast")
def forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    try:
        data = client.get_forecast(latitude=latitude, longitude=longitude)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve weather forecast.",
        ) from error

    hourly = data["hourly"]

    return {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            {
                "time": time,
                "temperature": temperature,
                "precipitation": precipitation,
                "humidity": humidity,
            }
            for time, temperature, precipitation, humidity in zip(
                hourly["time"],
                hourly["temperature_2m"],
                hourly["precipitation"],
                hourly["relative_humidity_2m"],
            )
        ],
    }