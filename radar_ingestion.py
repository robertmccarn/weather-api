import logging

from config import LOCATIONS
from radar.mrms import MRMSClient
from weather_database import WeatherDatabase


logger = logging.getLogger(__name__)


def run_radar_ingestion(
    database_path: str = "weather.db",
    locations=None,
    product: str = "1hr",
):
    selected_locations = LOCATIONS if locations is None else locations

    database = WeatherDatabase(database_path)
    client = MRMSClient()

    summary = {
        "locations_processed": 0,
        "locations_failed": 0,
    }

    try:
        database.create_tables()

        for location in selected_locations:
            try:
                observation = client.get_precipitation(
                    latitude=location["latitude"],
                    longitude=location["longitude"],
                    product=product,
                )

                database.save_radar_observation(
                    latitude=observation.latitude,
                    longitude=observation.longitude,
                    precipitation_inches=observation.precipitation_inches,
                    product=observation.product,
                    observed_at=observation.observed_at,
                )

                summary["locations_processed"] += 1

            except Exception:
                summary["locations_failed"] += 1
                logger.exception(
                    "Failed to ingest radar data for %s",
                    location["name"],
                )

        database.commit()

        logger.info(
            "Radar ingestion completed: %d locations processed, %d failed",
            summary["locations_processed"],
            summary["locations_failed"],
        )

        return summary

    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    run_radar_ingestion()
