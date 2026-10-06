from open_meteo import OpenMeteoClient
from weather_database import WeatherDatabase

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
    {
        "name": "Dallas, TX",
        "latitude": 32.7767,
        "longitude": -96.7970,
    },
]


database = WeatherDatabase("weather.db")
client = OpenMeteoClient()

database.create_tables()

for location in locations:
    database.add_location(
        location["name"],
        location["latitude"],
        location["longitude"],
    )

    location_id = database.get_location_id(location["name"])

    last_loaded_timestamp = database.get_watermark(location_id)

    data = client.get_forecast(
        latitude=location["latitude"],
        longitude=location["longitude"],
    )

    hourly = data["hourly"]

    times = hourly["time"]
    temperatures = hourly["temperature_2m"]
    precipitation = hourly["precipitation"]
    humidity = hourly["relative_humidity_2m"]

    records_processed = 0

    for time, temperature, rain, humidity_value in zip(
        times,
        temperatures,
        precipitation,
        humidity,
    ):
        if last_loaded_timestamp is not None:
            if time <= last_loaded_timestamp:
                continue

        database.save_weather(
            location_id,
            time,
            temperature,
            rain,
            humidity_value,
        )

        records_processed += 1

    database.commit()

    print(f"{location['name']}: {records_processed} records processed")

database.close()
