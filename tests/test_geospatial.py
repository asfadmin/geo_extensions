import pytest
from satlib.geospatial import _polygon_crosses_antimeridian, split_bbox_on_idl
from shapely.geometry import Polygon


@pytest.fixture
def centered_rectangle():
    """A rectanglular polygon centered at 0, 0"""

    return Polygon([
        (-30., 10.), (-30., -10.),
        (30., 10.), (30., -10.), (-30., 10.),
    ])


def test_polygon_crosses_antimeridian_simple(centered_rectangle):
    assert _polygon_crosses_antimeridian(centered_rectangle) is False


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
    assert _polygon_crosses_antimeridian(polygon) is False


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
    assert _polygon_crosses_antimeridian(polygon) is True


def test_split_bbox_on_idl_noop():
    bbox = [(60., 160.), (60., 170.), (70., 170.), (70., 160.), (60., 160.)]
    assert split_bbox_on_idl(bbox, include_closure_points=True) == [bbox]


def test_split_bbox_on_idl_clockwise_noop():
    bbox = [(60., 160.), (60., 170.), (70., 170.), (70., 160.), (60., 160.)][::-1]
    assert split_bbox_on_idl(bbox, include_closure_points=True) == [bbox]


def test_split_bbox_on_idl_meridian_noop():
    bbox = [(40., -10.), (30., -10.), (30., 10.), (40., 10.), (40., -10.)]
    assert split_bbox_on_idl(bbox, include_closure_points=True) == [bbox]


def test_split_bbox_on_idl_centered():
    """Polygon is centered on IDL"""
    bbox = [(60, 170), (60, -170), (70, -170), (70, 170), (60, 170)]
    assert split_bbox_on_idl(bbox) == [
        [(70.0, 179.999), (60.0, 179.999), (60.0, 170.0), (70.0, 170.0)],
        [(60.0, -179.999), (70.0, -179.999), (70.0, -170.0), (60.0, -170.0)],
    ]


def test_split_bbox_on_idl_centered_closure_points():
    """Polygon is centered on IDL and we return closure points"""
    bbox = [(60, 170), (60, -170), (70, -170), (70, 170), (60, 170)]
    assert split_bbox_on_idl(bbox, include_closure_points=True) == [
        [(70.0, 179.999), (60.0, 179.999), (60.0, 170.0), (70.0, 170.0), (70.0, 179.999)],
        [(60.0, -179.999), (70.0, -179.999), (70.0, -170.0), (60.0, -170.0), (60.0, -179.999)],
    ]


def test_split_bbox_on_idl_centered_closure_points_ccw():
    """Polygon is centered on IDL and we return closure points in ccw order"""
    bbox = [(60, 170), (60, -170), (70, -170), (70, 170), (60, 170)]
    assert split_bbox_on_idl(bbox, include_closure_points=True, ccw=True) == [
        [(70.0, 179.999), (70.0, 170.0), (60.0, 170.0), (60.0, 179.999), (70.0, 179.999)],
        [(60.0, -179.999), (60.0, -170.0), (70.0, -170.0), (70.0, -179.999), (60.0, -179.999)],
    ]


def test_split_bbox_on_idl_west():
    """Polygon is mostly west of the IDL"""
    bbox = [(60, 170), (60, -179), (70, -179), (70, 170), (60, 170)]
    assert split_bbox_on_idl(bbox) == [
        [(70.0, 179.999), (60.0, 179.999), (60.0, 170.0), (70.0, 170.0)],
        [(60.0, -179.999), (70.0, -179.999), (70.0, -179.0), (60.0, -179.0)],
    ]


def test_split_bbox_on_idl_east():
    """Polygon is mostly east of the IDL"""
    bbox = [(60, 179), (60, -170), (70, -170), (70, 179), (60, 179)]
    assert split_bbox_on_idl(bbox) == [
        [(70.0, 179.999), (60.0, 179.999), (60.0, 179.0), (70.0, 179.0)],
        [(60.0, -179.999), (70.0, -179.999), (70.0, -170.0), (60.0, -170.0)],
    ]


def test_split_bbox_on_idl_alos_example():
    """Example from ALOS mission: ALPSRP237090990-L1.1"""
    bbox = [
        (50.172, 179.648),
        (49.658, 179.794),
        (49.766, -179.255),
        (50.281, -179.392),
        (50.172, 179.648),
    ]
    assert split_bbox_on_idl(bbox) == [
        [
            (50.21196666666666, 179.999),
            (49.68139432176656, 179.999),
            (49.658, 179.79399999999998),
            (50.172, 179.64800000000002),
        ],
        [
            (49.68139432176656, -179.999),
            (50.21196666666666, -179.999),
            (50.281, -179.392),
            (49.766, -179.255),
        ],
    ]
