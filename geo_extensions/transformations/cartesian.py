"""Geospatial helpers for working in a cartesian coordinate system.

CMR has the following constraints for cartesian polygons:
    - Any single spatial area may not cross the International Date Line (unless
        it is a bounding box) or Poles.
    - Two vertices will be connected with a straight line.

Taken from: <https://wiki.earthdata.nasa.gov/spaces/CMR/pages/50036858/
CMR+Data+Partner+User+Guide#CMRDataPartnerUserGuide-CartesianCoordinateSystem>

This module contains helpers to fulfill the cartesian system CMR requirements.
"""

import math
from typing import cast

import shapely.ops
from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient

from geo_extensions.checks import (
    polygon_crosses_antimeridian_ccw,
    polygon_crosses_antimeridian_fixed_size,
)
from geo_extensions.types import Transformation, TransformationResult


def simplify_polygon(tolerance: float, preserve_topology: bool = True) -> Transformation:
    """CARTESIAN: Create a transformation that calls polygon.simplify.

    :param tolerance: coordinates of the simplified geometry will be no more
        than the tolerance distance from the original
    :param preserve_topology: unless the topology preserving option is used, the
        algorithm may produce self-intersecting or otherwise invalid geometries
    :returns: a callable transformation using the passed parameters
    """

    def simplify_polygon_transform(polygon: Polygon) -> TransformationResult:
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
    new_polygons = _split_polygon(shifted_polygon)

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
        new_polygons = _split_polygon(shifted_polygon)

        for polygon in new_polygons:
            yield _shift_polygon_back(polygon)

    return split_polygon_transform


def _shift_polygon(polygon: Polygon) -> Polygon:
    """Shift longitudes so an antimeridian crossing becomes contiguous"""
    if polygon.is_empty:
        return polygon

    coords = list(polygon.exterior.coords)

    # Which "period" each coord is on around the earth. I.e crossing the
    # antimeridian to the left will decrement the period for each coord after.
    revolutions = [0]

    prev_lon = coords[0][0]
    for lon, _ in coords[1:]:
        delta = lon - prev_lon
        prev_revolution = revolutions[-1]
        step = 0
        if delta > 180:
            step = -1
        elif delta < -180:
            step = 1
        revolutions.append(prev_revolution + step)
        prev_lon = lon

    # Normalize the lowest point into [0, 360), so no revolution is negative
    # and _split_polygon can count periods up from there.
    min_lon = min(lon + 360 * rev for (lon, _), rev in zip(coords, revolutions))
    revolutions = [int(rev - min_lon // 360) for rev in revolutions]

    # rev=0 points come out untouched; the rest move forward whole periods.
    return Polygon(
        [
            # ruff hint
            (lon + 360 * rev, lat)
            for (lon, lat), rev in zip(coords, revolutions)
        ]
    )


def _shift_polygon_back(polygon: Polygon) -> Polygon:
    """Shift back to [-180, 180] range."""

    min_lon, _, _, _ = polygon.bounds
    offset = (min_lon + 180) // 360 * 360

    return Polygon(
        [
            # ruff hint
            (lon - offset, lat)
            for lon, lat in polygon.exterior.coords
        ]
    )


def _split_polygon(polygon: Polygon) -> list[Polygon]:
    """Split on every antimeridian (180 + 360n) the polygon reaches across."""

    min_lon, _, max_lon, _ = polygon.bounds
    # Only antimeridians strictly inside the span can cut anything. A shape
    # wrapping the globe several times crosses several of them.
    first = int((min_lon - 180) // 360 + 1)
    last = math.ceil((max_lon - 180) / 360)

    polygons = [polygon]
    antimeridian_lons = (180 + 360 * n for n in range(first, last))
    for lon in antimeridian_lons:
        antimeridian = LineString([(lon, 90), (lon, -90)])
        polygons = [
            # ruff hint
            geom
            for poly in polygons
            for geom in shapely.ops.split(poly, antimeridian).geoms
            if isinstance(geom, Polygon)
        ]

    return [
        # ruff hint
        orient(poly)
        for poly in polygons
        if not _ignore_polygon(poly)
    ]


def _ignore_polygon(polygon: Polygon) -> bool:
    min_lon, _, max_lon, _ = polygon.bounds
    # We want to ignore any tiny slivers of polygons that might barely cross
    # the antimeridian. For CMR, the polygons don't need to be that precise
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
