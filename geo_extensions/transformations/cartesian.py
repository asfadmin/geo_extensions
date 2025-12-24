"""Geospatial helpers for working in a cartesian coordinate system.

CMR has the following constraints for cartesian polygons:
    - Any single spatial area may not cross the International Date Line (unless
        it is a bounding box) or Poles.
    - Two vertices will be connected with a straight line.

Taken from: <https://wiki.earthdata.nasa.gov/spaces/CMR/pages/50036858/
CMR+Data+Partner+User+Guide#CMRDataPartnerUserGuide-CartesianCoordinateSystem>

This module contains helpers to fulfill the cartesian system CMR requirements.
"""

from typing import cast

import shapely.ops
from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient

from geo_extensions.checks import (
    polygon_crosses_antimeridian_ccw,
    polygon_crosses_antimeridian_fixed_size,
)
from geo_extensions.types import Transformation, TransformationResult

ANTIMERIDIAN = LineString([(180, 90), (180, -90)])


def simplify_polygon(tolerance: float, preserve_topology: bool = True) -> Transformation:
    """CARTESIAN: Create a transformation that calls polygon.simplify.

    :returns: a callable transformation using the passed parameters
    """

    def simplify_polygon_transform(polygon: Polygon) -> TransformationResult:
        """Perform a shapely simplify operation on the polygon."""
        # NOTE(reweeden): I have been unable to produce a situation where a
        # polygon is simplified to a geometry other than Polygon.
        yield cast(
            Polygon,
            polygon.simplify(
                tolerance,
                preserve_topology=preserve_topology,
            ),
        )

    return simplify_polygon_transform


def split_polygon_on_antimeridian_ccw(polygon: Polygon) -> TransformationResult:
    """CARTESIAN: Perform adjustment when the polygon crosses the antimeridian
    and is known to be wound in counter clockwise order.

    CMR requires the polygon to be split into two separate polygons to avoid it
    being interpreted as wrapping the long way around the Earth.

    :param polygon: the polygon to split if necessary. Polygon must fulfill the
        following conditions:
            - Points must be in counter clockwise winding order
            - Polygon must not cover more than half of the earth
    :returns: a generator yielding the split polygons
    """

    if not polygon_crosses_antimeridian_ccw(polygon):
        yield polygon
        return

    shifted_polygon = _shift_polygon(polygon)
    new_polygons = _split_polygon(shifted_polygon, ANTIMERIDIAN)

    for polygon in new_polygons:
        yield _shift_polygon_back(polygon)


def split_polygon_on_antimeridian_fixed_size(
    min_lon_extent: float,
) -> Transformation:
    """CARTESIAN: Perform adjustment when the polygon crosses the antimeridian
    using a heuristic to determine if the polygon needs to be split.

    CMR requires the polygon to be split into two separate polygons to avoid it
    being interpreted as wrapping the long way around the Earth.

    :param min_lon_extent: the lower bound for the distance between the
        longitude values of the bounding box enclosing the entire polygon.
        Must be between (0, 180) exclusive.
    :returns: a callable transformation using the passed parameters
    """

    def split_polygon_transform(polygon: Polygon) -> TransformationResult:
        if not polygon_crosses_antimeridian_fixed_size(polygon, min_lon_extent):
            yield polygon
            return

        shifted_polygon = _shift_polygon(polygon)
        new_polygons = _split_polygon(shifted_polygon, ANTIMERIDIAN)

        for polygon in new_polygons:
            yield _shift_polygon_back(polygon)

    return split_polygon_transform


def _shift_polygon(polygon: Polygon) -> Polygon:
    """Shift into [0, 360) range."""

    return Polygon(
        [
            # ruff hint
            ((360.0 + lon) % 360, lat)
            for lon, lat in polygon.exterior.coords
        ]
    )


def _shift_polygon_back(polygon: Polygon) -> Polygon:
    """Shift back to [-180, 180] range."""

    _, _, max_lon, _ = polygon.bounds
    return Polygon(
        [
            # ruff hint
            (_adjust_lon(lon, max_lon), lat)
            for lon, lat in polygon.exterior.coords
        ]
    )


def _adjust_lon(lon: float, max_lon: float) -> float:
    if lon > 180.0:
        lon -= 360
    elif lon == 180.0 and max_lon != 180.0:
        lon = -180.0

    return lon


def _split_polygon(
    polygon: Polygon,
    line: LineString,
) -> list[Polygon]:
    split_collection = shapely.ops.split(polygon, line)

    return [
        # ruff hint
        orient(geom)
        for geom in split_collection.geoms
        if isinstance(geom, Polygon) and not _ignore_polygon(geom)
    ]


def _ignore_polygon(polygon: Polygon) -> bool:
    min_lon, _, max_lon, _ = polygon.bounds
    # We want to ignore any tiny slivers of polygons that might barely cross
    # the antimeridian. For CMR, the polygons don't need to be that precice
    # and we're rounding to 179.999 anyway. So realistically we don't want any
    # polygons that are contained within the +/-0.001 degrees around the
    # antimeridian. Due to possible floating point errors in the distance
    # calculation, we are a little generous in this trimming and set our
    # threshold to 0.0015 instead of just 0.001
    #
    # For instance:
    # >>> 180.001-180
    # 0.0010000000000047748
    # >>> 180.001-180 > .001
    # True

    return not (max_lon - min_lon > 0.0015)
