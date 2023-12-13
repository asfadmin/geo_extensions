import pytest
import shapely.geometry
import strategies
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from satlib.geospatial import (
    polygon_crosses_antimeridian,
    split_polygon_on_antimeridian,
)
from shapely.geometry import Polygon


@pytest.fixture
def rectangle():
    """A rectanglular polygon"""
    polygon = Polygon([
        (160., 60.), (170., 60.),
        (170., 70.), (160., 70.), (160., 60.),
    ])
    assert polygon.exterior.is_ccw

    return polygon


@pytest.fixture
def centered_rectangle():
    """A rectanglular polygon centered at 0, 0"""
    polygon = Polygon([
        (-30., 10.), (-30., -10.),
        (30., 10.), (30., -10.), (-30., 10.),
    ])
    assert polygon.exterior.is_ccw

    return polygon


@pytest.fixture
def antimeridian_centered_rectangle():
    """A rectanglular polygon centered over the antimeridian"""
    polygon = Polygon([
        (150., 10.), (150., -10.),
        (-150., -10.), (-150., 10.), (150., 10.),
    ])
    assert not polygon.exterior.is_ccw

    return polygon


def test_polygon_crosses_antimeridian_simple(centered_rectangle):
    assert polygon_crosses_antimeridian(centered_rectangle) is False


def test_polygon_crosses_antimeridian_tricky():
    r"""A polygon that looks something like this, centered at 0, 0:
        --------
        \      /
        /      \
        --------
    """
    polygon = Polygon([
        (-30., 10.), (-10., 0.), (-30., -10.),
        (30., 10.), (10., 0.), (30., -10.), (-30., 10.),
    ])
    assert polygon_crosses_antimeridian(polygon) is False


def test_polygon_crosses_antimeridian_tricky_crosses():
    r"""A polygon that looks something like this, crossing the IDL:
        --------
        \      /
        /      \
        --------
    """
    polygon = Polygon([
        (150., 10.), (170., 0.), (150., -10.),
        (-150., 10.), (-170., 0.), (-150., -10.), (150., 10.),
    ])
    assert polygon_crosses_antimeridian(polygon) is True


@given(polygon=strategies.rectangles())
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_split_polygon_on_antimeridian_returns_ccw(polygon):
    for poly in split_polygon_on_antimeridian(polygon):
        assert poly.exterior.is_ccw


@given(
    polygon=strategies.rectangles(
        # Very small polygons near the antimeridian will be culled.
        lons=st.floats(min_value=-179.990, max_value=180),
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_split_polygon_on_antimeridian_returns_non_empty_list(polygon):
    assert split_polygon_on_antimeridian(polygon)


def test_split_polygon_on_antimeridian_returns_empty_list():
    # There is a case where the input polygon is realy small, and both split
    # parts are culled.
    polygon = Polygon([
        (180, 1), (180, 0), (-179.999, 0), (-179.999, 1), (180, 1)
    ])
    assert split_polygon_on_antimeridian(polygon) == []


def test_split_polygon_on_antimeridian_noop(rectangle):
    assert split_polygon_on_antimeridian(rectangle) == [rectangle]


def test_split_bbox_on_idl_meridian_noop(centered_rectangle):
    assert split_polygon_on_antimeridian(centered_rectangle) == [centered_rectangle]


def test_split_polygon_on_antimeridian_centered(antimeridian_centered_rectangle):
    """Polygon is centered on IDL"""
    assert split_polygon_on_antimeridian(antimeridian_centered_rectangle) == [
        Polygon([
            (179.999, 10.), (150., 10.), (150., -10),
            (179.999, -10), (179.999, 10.)
        ]),
        Polygon([
            (-179.999, -10.), (-150., -10.), (-150., 10),
            (-179.999, 10), (-179.999, -10.)
        ])
    ]


def test_split_polygon_on_antimeridian_west():
    """Polygon is mostly west of the IDL"""
    polygon = Polygon([
        (170., 70.), (170., 60.), (-179., 60.),
        (-179., 70.), (170., 70.)
    ])
    assert not polygon.exterior.is_ccw

    assert split_polygon_on_antimeridian(polygon) == [
        Polygon([
            (179.999, 70.), (170., 70.), (170., 60.),
            (179.999, 60.), (179.999, 70.)
        ]),
        Polygon([
            (-179.999, 60.), (-179., 60.), (-179., 70.),
            (-179.999, 70.), (-179.999, 60.)
        ]),
    ]


def test_split_polygon_on_antimeridian_east():
    """Polygon is mostly east of the IDL"""
    polygon = Polygon([
        (179., 70.), (179., 60.), (-170., 60.),
        (-170., 70.), (179., 70.)
    ])
    assert not polygon.exterior.is_ccw

    assert split_polygon_on_antimeridian(polygon) == [
        Polygon([
            (179.999, 70.), (179., 70.), (179., 60.),
            (179.999, 60.), (179.999, 70.)
        ]),
        Polygon([
            (-179.999, 60.), (-170., 60.), (-170., 70.),
            (-179.999, 70.), (-179.999, 60.)
        ]),
    ]


def test_split_polygon_on_antimeridian_alos_example():
    """Example from ALOS mission: ALPSRP237090990-L1.1"""
    polygon = Polygon([
        (179.648, 50.172),
        (179.794, 49.658),
        (-179.255, 49.766),
        (-179.392, 50.281),
        (179.648, 50.172),
    ])
    polygons = split_polygon_on_antimeridian(polygon)

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (179.999, 50.21196666666666),
            (179.64800000000002, 50.172),
            (179.79399999999998, 49.658),
            (179.999, 49.68139432176656),
            (179.999, 50.21196666666666),
        ],
        [
            (-179.999, 49.68139432176656),
            (-179.255, 49.766),
            (-179.392, 50.281),
            (-179.999, 50.21196666666666),
            (-179.999, 49.68139432176656),
        ],
    ]


def test_split_polygon_on_antimeridian_opera_example():
    """Example from OPERA RTC Static layer:

    OPERA_L2_RTC-S1-STATIC_T001-000677-IW2_20140403_S1A_30_v1.0
    """
    north, west, south, east = (
        66.663,
        178.834,
        66.140,
        -178.918,
    )
    polygon = shapely.geometry.box(east, north, west, south, ccw=True)
    polygons = split_polygon_on_antimeridian(polygon)

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (179.999, 66.663),
            (178.83400000000006, 66.663),
            (178.83400000000006, 66.140),
            (179.999, 66.140),
            (179.999, 66.663),
        ],
        [
            (-179.999, 66.140),
            (-178.918, 66.140),
            (-178.918, 66.663),
            (-179.999, 66.663),
            (-179.999, 66.140),
        ],
    ]
