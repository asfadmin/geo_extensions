from typing import Iterable, List, Sequence, Tuple

from shapely import Geometry, wkt
from shapely.geometry import MultiPolygon, Polygon, shape

from geo_extensions.types import Transformation, TransformationResult


class Transformer:
    """Apply a sequence of transformations to a polygon list."""

    def __init__(self, transformations: Sequence[Transformation]):
        self.transformations = transformations

    def from_geo_json(self, geo_json: dict) -> List[Polygon]:
        """Load and transform an object from a GeoJSON dict.

        :returns: a list of transformed polygons
        :raises: ShapelyError, Exception
        """

        obj = shape(geo_json)
        polygons = to_polygons(obj)

        return self.transform(polygons)

    def from_wkt(self, wkt_str: str) -> List[Polygon]:
        """Load and transform an object from a WKT string.

        :returns: a list of transformed polygons
        :raises: ShapelyError, Exception
        """

        obj = wkt.loads(wkt_str)
        polygons = to_polygons(obj)

        return self.transform(polygons)

    def transform(self, polygons: Iterable[Polygon]) -> List[Polygon]:
        """Perform the transformation chain on a sequence of polygons.

        :returns: a list of transformed polygons
        """

        return list(
            _apply_transformations(
                polygons,
                tuple(self.transformations),
            )
        )


def to_polygons(obj: Geometry) -> TransformationResult:
    """Convert a geometry to a sequence of polygons.

    :returns: a generator yielding the polygon sequence.
    :raises: Exception
    """
    if isinstance(obj, MultiPolygon):
        for poly in obj.geoms:
            yield poly
        return

    if isinstance(obj, Polygon):
        yield obj
        return

    raise Exception(f"WKT: '{obj}' is not a Polygon or MultiPolygon")


def _apply_transformations(
    polygons: Iterable[Polygon],
    transformations: Tuple[Transformation, ...],
) -> TransformationResult:
    if not transformations:
        yield from polygons
        return

    transformation, transformations = transformations[0], transformations[1:]
    for polygon in polygons:
        yield from _apply_transformations(
            transformation(polygon),
            transformations,
        )
