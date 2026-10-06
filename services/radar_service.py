from radar.mrms import MRMSClient, RadarObservation


class RadarService:
    def __init__(self, client: MRMSClient):
        self.client = client

    def get_point_precipitation(
        self,
        latitude: float,
        longitude: float,
        product: str = "1hr",
    ) -> RadarObservation:
        return self.client.get_precipitation(
            latitude,
            longitude,
            product,
        )

    def get_points_precipitation(
        self,
        coordinates: list[tuple[float, float]],
        product: str = "1hr",
    ) -> list[RadarObservation]:
        return [
            self.get_point_precipitation(latitude, longitude, product)
            for latitude, longitude in coordinates
        ]
