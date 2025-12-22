from pathlib import Path

import pytest
from shapely.geometry import Polygon


@pytest.fixture(scope="session")
def data_path():
    return Path(__file__).parent / "data"


@pytest.fixture
def rectangle():
    """A rectanglular polygon"""
    polygon = Polygon(
        [
            (160.0, 60.0),
            (170.0, 60.0),
            (170.0, 70.0),
            (160.0, 70.0),
            (160.0, 60.0),
        ]
    )
    assert polygon.exterior.is_ccw
    assert polygon.exterior.is_valid

    return polygon


@pytest.fixture
def centered_rectangle():
    """A rectanglular polygon centered at 0, 0"""
    polygon = Polygon(
        [
            (-30.0, 10.0),
            (-30.0, -10.0),
            (30.0, -10.0),
            (30.0, 10.0),
            (-30.0, 10.0),
        ]
    )
    assert polygon.exterior.is_ccw
    assert polygon.exterior.is_valid

    return polygon


@pytest.fixture
def antimeridian_centered_rectangle():
    """A rectanglular polygon centered over the antimeridian"""
    polygon = Polygon(
        [
            (150.0, 10.0),
            (150.0, -10.0),
            (-150.0, -10.0),
            (-150.0, 10.0),
            (150.0, 10.0),
        ]
    )
    assert not polygon.exterior.is_ccw
    assert polygon.exterior.is_valid

    return polygon


@pytest.fixture
def multi_crossing_polygon():
    r"""A polygon that looks something like this, crossing back and forth
    accross the IDL multiple times:
        --------
        |      /
        |      \
        --------
    """
    polygon = Polygon(
        [
            (150.0, -10.0),
            (-150.0, -10.0),
            (160.0, 0.0),
            (-150.0, 10.0),
            (150.0, 10.0),
            (150.0, -10.0),
        ]
    )
    assert not polygon.exterior.is_ccw
    assert not polygon.exterior.is_valid

    return polygon
