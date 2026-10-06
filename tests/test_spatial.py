import pytest

from spatial.coordinates import haversine_distance_km, validate_coordinate
from spatial.sampling import deduplicate_points, grid_points, interpolate_points


def test_haversine_distance_is_zero_for_same_point():
    assert haversine_distance_km(30, -95, 30, -95) == pytest.approx(0)


def test_haversine_distance_between_houston_and_dallas():
    distance = haversine_distance_km(
        29.7604,
        -95.3698,
        32.7767,
        -96.7970,
    )

    assert distance == pytest.approx(362, abs=3)


def test_validate_coordinate_rejects_invalid_latitude():
    with pytest.raises(ValueError):
        validate_coordinate(91, -95)


def test_interpolate_points_includes_endpoints():
    points = interpolate_points(30, -95, 32, -96, 3)

    assert points == [
        (30.0, -95.0),
        (31.0, -95.5),
        (32.0, -96.0),
    ]


def test_interpolate_points_requires_two_or_more_points():
    with pytest.raises(ValueError):
        interpolate_points(30, -95, 32, -96, 1)


def test_grid_points_returns_expected_count():
    points = grid_points(30, 32, -96, -95, 3, 2)

    assert len(points) == 6
    assert points[0] == (30.0, -96.0)
    assert points[-1] == (32.0, -95.0)


def test_deduplicate_points_uses_coordinate_precision():
    points = deduplicate_points([
        (30.000001, -95.000001),
        (30.000002, -95.000002),
        (31.0, -96.0),
    ])

    assert len(points) == 2
