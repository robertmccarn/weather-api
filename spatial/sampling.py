from typing import Iterable

from .coordinates import validate_coordinate


def interpolate_points(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
    count: int,
) -> list[tuple[float, float]]:
    if count < 2:
        raise ValueError("count must be at least 2.")

    validate_coordinate(start_latitude, start_longitude)
    validate_coordinate(end_latitude, end_longitude)

    return [
        (
            start_latitude
            + (end_latitude - start_latitude) * fraction,
            start_longitude
            + (end_longitude - start_longitude) * fraction,
        )
        for fraction in (
            index / (count - 1)
            for index in range(count)
        )
    ]


def grid_points(
    min_latitude: float,
    max_latitude: float,
    min_longitude: float,
    max_longitude: float,
    rows: int,
    columns: int,
) -> list[tuple[float, float]]:
    if rows < 1 or columns < 1:
        raise ValueError("rows and columns must be at least 1.")

    validate_coordinate(min_latitude, min_longitude)
    validate_coordinate(max_latitude, max_longitude)

    if min_latitude > max_latitude:
        raise ValueError("min_latitude must not exceed max_latitude.")
    if min_longitude > max_longitude:
        raise ValueError("min_longitude must not exceed max_longitude.")

    latitudes = [
        min_latitude
        if rows == 1
        else min_latitude
        + (max_latitude - min_latitude) * index / (rows - 1)
        for index in range(rows)
    ]
    longitudes = [
        min_longitude
        if columns == 1
        else min_longitude
        + (max_longitude - min_longitude) * index / (columns - 1)
        for index in range(columns)
    ]

    return [
        (latitude, longitude)
        for latitude in latitudes
        for longitude in longitudes
    ]


def deduplicate_points(
    points: Iterable[tuple[float, float]],
    precision: int = 5,
) -> list[tuple[float, float]]:
    seen = set()
    result = []

    for latitude, longitude in points:
        key = (round(latitude, precision), round(longitude, precision))
        if key not in seen:
            seen.add(key)
            result.append((latitude, longitude))

    return result
