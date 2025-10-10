"""Geospatial helpers for working in a geodetic coordinate system.

CMR has the following constraints for geodetic polygons:
    - The implemented Geodetic model uses the great circle distance to connect
        two vertices for constructing a polygon area or line. If there is not
        enough density (that is, the number of points) for a set of vertices,
        then the line or the polygon area might be misinterpreted or the
        metadata might be considered invalid.
    - Any single spatial area may cross the International Date Line and/or Poles.
    - Any single spatial area may not cover more than one half of the earth.

Taken from: <https://wiki.earthdata.nasa.gov/spaces/CMR/pages/50036858/
CMR+Data+Partner+User+Guide#CMRDataPartnerUserGuide-GeodeticCoordinateSystem>

This module contains helpers to fulfill the geodetic system CMR requirements.
"""

import itertools
from collections.abc import Generator
from typing import TypeVar

from pygeodesy.sphericalTrigonometry import LatLon
from shapely.coords import CoordinateSequence
from shapely.geometry import Polygon

from geo_extensions.types import Transformation, TransformationResult

T = TypeVar("T")


def densify_polygon(tolerance_meters: float) -> Transformation:
    """GEODETIC: Create a transformation that increases the point density of a
    polygon along great circle arcs between each point.

    In a sense, this is an opposite operation from 'simplify'.

    :param tolerance_meters: The maximum allowable cross track error between
        a line segment when interpreted as a cartesian point. Must be greater
        than 0.
    :returns: a callable transformation using the passed parameters
    """
    if tolerance_meters <= 0:
        raise ValueError("'tolerance_meters' must be greater than 0")

    def densify(polygon: Polygon) -> TransformationResult:
        """Densify the polygon by adding additional points along the great
        circle arcs between the existing points.
        """
        yield Polygon(
            shell=_densify_ring(polygon.exterior.coords, tolerance_meters),
            holes=[
                _densify_ring(interior.coords, tolerance_meters)
                for interior in polygon.interiors
            ],
        )

    return densify


def _densify_ring(
    coords: CoordinateSequence,
    tolerance_meters: float,
) -> Generator[tuple[float, ...]]:
    assert tolerance_meters > 0

    if len(coords) < 2:
        yield from coords
        return

    for c1, c2 in itertools.pairwise(coords):
        p1 = _shapely_to_pygeodesy(c1)
        p2 = _shapely_to_pygeodesy(c2)

        yield c1

        for p_new in _densify_edge(p1, p2, tolerance_meters):
            yield (p_new.lon, p_new.lat)

    yield c2


def _densify_edge(p1: LatLon, p2: LatLon, tolerance_meters: float) -> Generator[LatLon]:
    # Cartesian midpoint
    c_mid_cartesian = ((p1.lon + p2.lon) / 2, (p1.lat + p2.lat) / 2)
    p_mid_cartesian = _shapely_to_pygeodesy(c_mid_cartesian)

    error_meters = abs(p_mid_cartesian.crossTrackDistanceTo(p1, p2))
    if error_meters < tolerance_meters:
        return

    # Add a point in the middle and recursively densify the resulting edges
    p_mid = p1.midpointTo(p2)
    yield from _densify_edge(p1, p_mid, tolerance_meters)
    yield p_mid
    yield from _densify_edge(p_mid, p2, tolerance_meters)


def _shapely_to_pygeodesy(coord: tuple[float, ...]) -> LatLon:
    return LatLon(coord[1], coord[0])
