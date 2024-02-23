from shapely.geometry import Polygon

from geo_extensions.checks import (
    fixed_size_polygon_crosses_antimeridian,
    polygon_crosses_antimeridian,
)


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


def test_fixed_size_polygon_crosses_antimeridian_simple(centered_rectangle):
    assert fixed_size_polygon_crosses_antimeridian(centered_rectangle, 20) is False
    assert fixed_size_polygon_crosses_antimeridian(centered_rectangle, 179) is True


def test_fixed_size_polygon_crosses_antimeridian_tricky_crosses():
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
    assert fixed_size_polygon_crosses_antimeridian(polygon, 30) is True
