"""Geospatial aware polygon tests.

When polygons are required to be in counter-clockwise order, this means counter-
clockwise in the real world, on the surface of the Earth. Specifically, polygons
MUST NOT be oriented using the shapely `orient` function, as this function
treats polygons as existing on an infinite flat plane and may end up actually
mis-ordering the polygons. Knowing that a polygon is in fact counter-clockwise
ordered on the surface of the Earth makes the shapely `is_ccw` property a very
useful and easy check to determine if the polygon crosses the antimeridian, as
in this case, the polygon will appear to be mis-ordered in the infinite flat
plane space.
"""

from shapely.geometry import Polygon


def polygon_crosses_antimeridian_ccw(polygon: Polygon) -> bool:
    """Checks if the longitude coordinates 'wrap around' the 180/-180 line.

    :param polygon: the polygon to check, must be known to be in counter-
        clockwise order.
    :returns: true if the polygon crosses the antimeridian
    """

    # Polygons crossing the antimeridian will appear to be mis-ordered or
    # crossing themselves
    return not (polygon.exterior.is_ccw and polygon.exterior.is_valid)


def polygon_crosses_antimeridian_fixed_size(
    polygon: Polygon,
    min_lon_extent: float,
) -> bool:
    """Checks if the longitude coordinates 'wrap around' the 180/-180 line
    based on a heuristic that assumes the polygon is of a certain size.

    :param polygon: the polygon check
    :param min_lon_extent: the lower bound for the distance between the
        longitude values of the bounding box enclosing the entire polygon.
        Must be between (0, 180) exclusive.
    :returns: true if the polygon crosses the antimeridian
    """
    assert 0 < min_lon_extent < 180

    min_lon, _, max_lon, _ = polygon.bounds
    dist_from_180 = 180 - min_lon_extent

    return max_lon > dist_from_180 or min_lon < -dist_from_180
