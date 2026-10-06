import logging
from datetime import datetime, timedelta

from config import REFRESH_HOURS


logger = logging.getLogger(__name__)


class WeatherIngestion:
    def __init__(self, database, client, locations):
        self.database = database
        self.client = client
        self.locations = locations

    def run(self):
        logger.info("Starting weather ingestion")

        summary = {
            "locations_processed": 0,
            "locations_failed": 0,
            "records_processed": 0,
        }

        for location in self.locations:
            try:
                records_processed = self._process_location(location)
                summary["locations_processed"] += 1
                summary["records_processed"] += records_processed
            except Exception:
                summary["locations_failed"] += 1
                logger.exception(
                    "Failed to process %s",
                    location["name"],
                )

        logger.info(
            "Weather ingestion completed: %d locations processed, "
            "%d failed, %d records processed",
            summary["locations_processed"],
            summary["locations_failed"],
            summary["records_processed"],
        )

        return summary

    def _process_location(self, location):
        try:
            self.database.add_location(
                location["name"],
                location["latitude"],
                location["longitude"],
            )

            location_id = self.database.get_location_id(
                location["name"]
            )

            last_loaded_timestamp = self.database.get_watermark(
                location_id
            )

            refresh_cutoff = None

            if last_loaded_timestamp is not None:
                last_loaded = datetime.fromisoformat(
                    last_loaded_timestamp
                )
                refresh_cutoff = (
                    last_loaded - timedelta(hours=REFRESH_HOURS)
                )

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
                if refresh_cutoff is not None:
                    current_time = datetime.fromisoformat(time)

                    if current_time < refresh_cutoff:
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

            return records_processed

        except Exception:
            self.database.rollback()
            raise
