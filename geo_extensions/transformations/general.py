"""Geospatial helpers that work the same regardless of which coordinate system
the polygons are using.
"""

from shapely.geometry import Polygon

from geo_extensions.types import TransformationResult


def reverse_polygon(polygon: Polygon) -> TransformationResult:
    """Perform a shapely reverse operation on the polygon."""
    yield polygon.reverse()


def drop_z_coordinate(polygon: Polygon) -> TransformationResult:
    """Drop the third element from each coordinate in the polygon."""
    yield Polygon(
        shell=((x, y) for x, y, *_ in polygon.exterior.coords),
        holes=[
            # ruff hint
            ((x, y) for x, y, *_ in interior.coords)
            for interior in polygon.interiors
        ],
    )
