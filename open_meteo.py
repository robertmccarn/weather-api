import requests


class OpenMeteoClient:
    API_URL = "https://api.open-meteo.com/v1/forecast"

    def get_forecast(self, latitude, longitude):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation,relative_humidity_2m",
        }

        response = requests.get(
            self.API_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()
