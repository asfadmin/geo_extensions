"""Geospatial helpers that work the same regardless of which coordinate system
the polygons are using.
"""

from typing import SupportsIndex

from shapely.geometry import Polygon

from geo_extensions.types import Transformation, TransformationResult


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


def round_points(ndigits: SupportsIndex) -> Transformation:
    """Create a transformation that rounds polygon points to a given number of
    digits.

    :returns: a callable transformation using the passed parameters
    """

    def round_points_(polygon: Polygon) -> TransformationResult:
        """Round the polygon's points."""
        yield Polygon(
            shell=(_round_coord(coord, ndigits) for coord in polygon.exterior.coords),
            holes=[
                # ruff hint
                (_round_coord(coord, ndigits) for coord in interior.coords)
                for interior in polygon.interiors
            ],
        )

    return round_points_


def _round_coord(
    coords: tuple[float, ...],
    ndigits: SupportsIndex,
) -> tuple[float, ...]:
    return tuple(round(x, ndigits) for x in coords)
