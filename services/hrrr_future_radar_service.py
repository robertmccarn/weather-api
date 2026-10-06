from datetime import datetime, timedelta, timezone
from typing import Any

import requests


class HRRRFutureRadarService:
    METADATA_URL = (
        "https://mesonet.agron.iastate.edu/data/gis/images/4326/"
        "hrrr/refd_1080.json"
    )

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_model_init(self) -> datetime:
        response = requests.get(self.METADATA_URL, timeout=self.timeout)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()

        value = payload.get("model_init_utc")
        if not value:
            raise ValueError("IEM HRRR metadata did not include model_init_utc.")

        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)

        text = str(value).replace("Z", "+00:00")
        model_init = datetime.fromisoformat(text)
        if model_init.tzinfo is None:
            model_init = model_init.replace(tzinfo=timezone.utc)
        return model_init.astimezone(timezone.utc)

    def get_next_six_hours(self) -> dict[str, Any]:
        model_init = self.get_model_init()
        now = datetime.now(timezone.utc)

        candidates = []
        for minute in range(15, 18 * 60 + 1, 15):
            valid_at = model_init + timedelta(minutes=minute)
            if valid_at < now:
                continue
            candidates.append(
                {
                    "forecast_minute": minute,
                    "valid_at": valid_at.isoformat(),
                    "layer": f"REFP-F{minute:04d}",
                }
            )
            if len(candidates) == 24:
                break

        if len(candidates) < 24:
            raise ValueError("IEM did not provide six hours of future HRRR frames.")

        return {
            "model": "HRRR",
            "model_init_utc": model_init.isoformat(),
            "frames": candidates,
        }
