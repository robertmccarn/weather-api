import pytest

from spatial.coordinates import haversine_distance_km, validate_coordinate


def test_validate_coordinate_accepts_valid_coordinates():
    validate_coordinate(30.0799, -95.4172)


@pytest.mark.parametrize(
    "latitude,longitude",
    [(91, 0), (-91, 0), (0, 181), (0, -181)],
)
def test_validate_coordinate_rejects_out_of_range(latitude, longitude):
    with pytest.raises(ValueError):
        validate_coordinate(latitude, longitude)


def test_haversine_distance_is_zero_for_same_point():
    assert haversine_distance_km(30, -95, 30, -95) == pytest.approx(0)


def test_haversine_distance_is_symmetric():
    first = haversine_distance_km(30, -95, 31, -94)
    second = haversine_distance_km(31, -94, 30, -95)
    assert first == pytest.approx(second)
