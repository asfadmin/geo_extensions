"""Geospatial helpers to prepare spatial extents for submission to CMR.

CMR has the following constraints on spatial extents:
    - The implemented Geodetic model uses the great circle distance to connect
        two vertices for constructing a polygon area or line. If there is not
        enough density (that is, the number of points) for a set of vertices,
        then the line or the polygon area might be misinterpreted or the
        metadata might be considered invalid.
    - Any single spatial area may cross the International Date Line and/or Poles
    - Any single spatial area may not cover more than one half of the earth.

Taken from: https://wiki.earthdata.nasa.gov/pages/viewpage.action?spaceKey=CMR&title=CMR+Data+Partner+User+Guide

There are also additional constraints that depend on the data format being used.
For UMM-G polygons must
    - Be counter clockwise ordered
    - Include closure points

A table describing the differences between data format requirements can be found here:
https://wiki.earthdata.nasa.gov/display/CMR/Polygon+Support+in+CMR+Search+and+Ingest+Interfaces

There are several challenges with representing polygons on a spherical surface,
the primary being that since all straight lines will 'wrap around' the surface,
it becomes impossible to unabmiguously define a polygon using only an ordered
set of points. This is the primary reason for the CMR requirements, as those
additional constraints make it possible to determine exactly which area is
meant by a set of points. Unfortunately, the polygons that we get from the data
provider won't necessarily meet those same requirements and we must use mission
specific knowledge to convert them to an unambiguous set of polygons to be used
by CMR.

This module aims to assist in that conversion to unambiguous polygons using the
CMR additional requirements. Any polygons passed in as arguments or returned
from functions in this module are assumed to be in counter clockwise order as
seen in the spherical space. This makes detecting whether a polygon crosses the
antimeridian (wraps around the edge of the flat coordinate system) very easy
even in the general case, because such a polygon will appear to be clockwise
ordered in the shapely flat space.
"""

from typing import List, Tuple

from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import linemerge, polygonize, unary_union

Point = Tuple[float, float]
Bbox = List[Point]

ANTIMERIDIAN = LineString([(180, 90), (180, -90)])

# Test!
def split_polygon_on_antimeridian(polygon: Polygon) -> List[Polygon]:
    """Perform adjustment when the polygon crosses the antimeridian.

    CMR requires the polygon to be split into two separate polygons to avoid it
    being interpreted as wrapping the long way around the Earth.

    :param polygon: the polygon to split if necessary. Polygon must fulfill the
        following conditions:
            - Points must be in counter clockwise winding order
            - Polygon must not cover more than half of the earth
    """

    if not polygon_crosses_antimeridian(polygon):
        return [polygon]

    shifted_polygon = _shift_polygon(polygon)
    new_polygons = _split_polygon(shifted_polygon, ANTIMERIDIAN)

    return [
        _shift_polygon_back(polygon)
        for polygon in new_polygons
    ]


def polygon_crosses_antimeridian(polygon: Polygon) -> bool:
    """Checks if the longitude coordinates 'wrap around' the 180/-180 line.

    The polygon must be oriented in counter-clockwise order.
    """

    # Polygons crossing the antimeridian will appear to be mis-ordered
    return not polygon.exterior.is_ccw


def fixed_size_polygon_crosses_antimeridian(
    polygon: Polygon,
    min_lon_extent: float,
) -> bool:
    """Checks if the longitude coordinates 'wrap around' the 180/-180 line
    based on a heuristic that assumes the polygon is of a certain size.

    :param polygon: the polygon check.
    :param min_lon_extent: the lower bound for the distance between the
        longitude values of the bounding box enclosing the entire polygon.
        Must be between (0, 180) exclusive.
    """
    assert 0 < min_lon_extent < 180

    min_lon, _, max_lon, _ = polygon.bounds
    dist_from_180 = 180 - min_lon_extent

    return max_lon > dist_from_180 or min_lon < -dist_from_180


def _shift_polygon(polygon: Polygon) -> Polygon:
    """Shift into 0-360 range."""

    return Polygon([
        ((360.0 + lon) % 360, lat)
        for lon, lat in polygon.boundary.coords
    ])


def _shift_polygon_back(polygon: Polygon) -> Polygon:
    """Shift back to -180-180 range.

    Also replaces points that land right on +/-180 with +/-179.999.
    """

    _, _, max_lon, _ = polygon.bounds
    return Polygon([
        (_adjust_lon(lon, max_lon), lat)
        for lon, lat in polygon.boundary.coords
    ])


def _adjust_lon(lon: float, max_lon: float) -> float:
    if lon > 180.0:
        return lon - 360
    elif lon == 180.0 and max_lon == 180.0:
        return 179.999
    elif lon == 180.0:
        return -179.999

    return lon


def _split_polygon(
    polygon: Polygon,
    line: LineString
) -> List[Polygon]:
    """Polygon and line must intersect."""

    merged = linemerge([polygon.boundary, line])
    borders = unary_union(merged)

    return [
        orient(poly)
        for poly in polygonize(borders)
        if not _ignore_polygon(poly)
    ]


def _ignore_polygon(polygon: Polygon) -> bool:
    min_lon, _, max_lon, _ = polygon.bounds
    # We want to ignore any tiny slivers of polygons that might barely cross
    # the antimeridian. For CMR, the polygons don't need to be that precice
    # and we're rounding to 179.999 anyway. So realistically we don't want any
    # polygons that are contained within the +/-0.001 degrees around the
    # antimeridian. Due to possible floating point errors in the distance
    # calculation, we are a little generous in this trimming and set our
    # threshold to 0.0015 instead of just 0.0015
    #
    # For instance:
    # >>> 180.001-180
    # 0.0010000000000047748
    # >>> 180.001-180 > .001
    # True

    return not (max_lon - min_lon > 0.0015)
