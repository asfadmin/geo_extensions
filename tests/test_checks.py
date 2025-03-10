from shapely.geometry import Polygon

from geo_extensions.checks import (
    polygon_crosses_antimeridian_ccw,
    polygon_crosses_antimeridian_fixed_size,
)


def test_polygon_crosses_antimeridian_ccw_simple(centered_rectangle):
    assert polygon_crosses_antimeridian_ccw(centered_rectangle) is False


def test_polygon_crosses_antimeridian_ccw_tricky():
    r"""A polygon that looks something like this, centered at 0, 0:
        --------
        \      /
        /      \
        --------
    """
    polygon = Polygon([
        (-30., 10.), (-10., 0.), (-30., -10.),
        (30., -10.), (10., 0.), (30., 10.), (-30., 10.),
    ])
    assert polygon_crosses_antimeridian_ccw(polygon) is False


def test_polygon_crosses_antimeridian_ccw_tricky_crosses():
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
    assert polygon_crosses_antimeridian_ccw(polygon) is True


def test_polygon_crosses_antimeridian_ccw_tricky_crosses_multiple_times(
    multi_crossing_polygon,
):
    assert polygon_crosses_antimeridian_ccw(multi_crossing_polygon) is True


def test_polygon_crosses_antimeridian_ccw_alos2_antarctica():
    """A polygon where three points are on one side and one point is on the
    other side of the antimeridian line.

    ALOS2 granule: ALOS2075945400-151019-WBDR1.1__D
    """
    polygon = Polygon([
        (-178.328, -79.438),
        (179.625, -76.163),
        (166.084, -76.163),
        (164.037, -79.438),
    ])

    assert polygon_crosses_antimeridian_ccw(polygon) is True


def test_polygon_crosses_antimeridian_fixed_size_simple(centered_rectangle):
    assert polygon_crosses_antimeridian_fixed_size(centered_rectangle, 20) is False
    assert polygon_crosses_antimeridian_fixed_size(centered_rectangle, 179) is True


def test_polygon_crosses_antimeridian_fixed_size_tricky_crosses():
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
    assert polygon_crosses_antimeridian_fixed_size(polygon, 30) is True


def test_polygon_crosses_antimeridian_fixed_size_antarctica():
    r"""A real polygon from ALOS2 granule ALOS2014555550-140830 which is located
    close to the south pole, and also crosses the antimeridian
    """
    polygon = Polygon([
        (-164.198, -82.125), (172.437, -83.885), (165.618, -80.869),
        (-176.331, -79.578), (-164.198, -82.125),
    ])
    assert polygon_crosses_antimeridian_fixed_size(polygon, 40) is True
