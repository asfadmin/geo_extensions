from shapely.geometry import Polygon


def polygon_crosses_antimeridian_ccw(polygon: Polygon) -> bool:
    """Checks if the longitude coordinates 'wrap around' the 180/-180 line.

    The polygon must be oriented in counter-clockwise order.

    :param polygon: the polygon to check
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
    """
    assert 0 < min_lon_extent < 180

    min_lon, _, max_lon, _ = polygon.bounds
    dist_from_180 = 180 - min_lon_extent

    return max_lon > dist_from_180 or min_lon < -dist_from_180
