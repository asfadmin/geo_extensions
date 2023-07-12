import pytest
from satlib.framing import center_lat_to_esa_frame, esa_frame_to_center_lat


@pytest.mark.parametrize(
    "center_lat,frame",
    (
        (0.0, 0),
        (90.0, 1800),
        (-90.0, 5400),
        (-89.95, 5401),
        (45.0, 900),
        (-45.0, 6300),
        (65.0, 1300),
        (-65.0, 5900),
        (1.0, 20),
        (-1.0, 7180),
        (0.05, 1),
        (-0.05, 7199),
    ),
)
def test_center_lat_to_esa_frame_ascending(center_lat, frame):
    assert center_lat_to_esa_frame(center_lat, ascending=True) == frame


@pytest.mark.parametrize(
    "center_lat,frame",
    (
        (0.0, 3600),
        (90.0, 1800),
        (-90.0, 5400),
        (-89.95, 5399),
        (45.0, 2700),
        (-45.0, 4500),
        (65.0, 2300),
        (-65.0, 4900),
        (1.0, 3580),
        (-1.0, 3620),
        (0.05, 3599),
        (-0.05, 3601),
    ),
)
def test_center_lat_to_esa_frame_descending(center_lat, frame):
    assert center_lat_to_esa_frame(center_lat, ascending=False) == frame


def test_esa_frame_to_center_lat():
    for frame in range(7200):
        center_lat, ascending = esa_frame_to_center_lat(frame)
        assert center_lat_to_esa_frame(center_lat, ascending=ascending) == frame
