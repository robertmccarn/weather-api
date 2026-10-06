import logging

logger = logging.getLogger(__name__)


class WeatherIngestion:
    def __init__(self, database, client, locations):
        self.database = database
        self.client = client
        self.locations = locations

    def run(self):
        logger.info("Starting weather ingestion")

        for location in self.locations:
            try:
                self._process_location(location)
            except Exception:
                logger.exception(
                    "Failed to process %s",
                    location["name"],
                )

        logger.info("Weather ingestion completed")

    def _process_location(self, location):
        try:
            self.database.add_location(
                location["name"],
                location["latitude"],
                location["longitude"],
            )

            location_id = self.database.get_location_id(location["name"])

            last_loaded_timestamp = self.database.get_watermark(location_id)

            data = self.client.get_forecast(
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

                self.database.save_weather(
                    location_id,
                    time,
                    temperature,
                    rain,
                    humidity_value,
                )

                records_processed += 1

            self.database.commit()

            logger.info(
                "%s: %d records processed",
                location["name"],
                records_processed,
            )

        except Exception:
            self.database.rollback()
            raise
