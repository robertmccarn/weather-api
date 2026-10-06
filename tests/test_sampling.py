import pytest

from spatial.sampling import deduplicate_points, grid_points, interpolate_points


def test_interpolate_points_includes_endpoints():
    points = interpolate_points(30, -95, 31, -94, 3)
    assert points == [(30, -95), (30.5, -94.5), (31, -94)]


def test_interpolate_points_requires_two_points():
    with pytest.raises(ValueError):
        interpolate_points(30, -95, 31, -94, 1)


def test_grid_points_creates_expected_grid():
    points = grid_points(30, 31, -95, -94, 2, 3)
    assert len(points) == 6
    assert points[0] == (30, -95)
    assert points[-1] == (31, -94)


def test_grid_points_rejects_invalid_bounds():
    with pytest.raises(ValueError):
        grid_points(31, 30, -95, -94, 2, 2)


def test_deduplicate_points_preserves_first_occurrence():
    points = [(30.0, -95.0), (30.000001, -95.000001), (31.0, -94.0)]
    assert deduplicate_points(points, precision=4) == [
        (30.0, -95.0),
        (31.0, -94.0),
    ]
