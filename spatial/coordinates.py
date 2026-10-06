from math import atan2, cos, radians, sin, sqrt


EARTH_RADIUS_KM = 6371.0088


def validate_coordinate(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")


def haversine_distance_km(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
) -> float:
    validate_coordinate(latitude1, longitude1)
    validate_coordinate(latitude2, longitude2)

    lat1 = radians(latitude1)
    lat2 = radians(latitude2)
    delta_lat = lat2 - lat1
    delta_lon = radians(longitude2 - longitude1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * atan2(sqrt(a), sqrt(1 - a))
