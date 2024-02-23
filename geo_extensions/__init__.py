from geo_extensions.checks import (
    fixed_size_polygon_crosses_antimeridian,
    polygon_crosses_antimeridian,
)
from geo_extensions.transformations import (
    reverse_polygon,
    simplify_polygon,
    split_polygon_on_antimeridian,
)
from geo_extensions.transformer import Transformer, to_polygons
from geo_extensions.types import Transformation, TransformationResult

default_transformer = Transformer([
    simplify_polygon(0.1),
    split_polygon_on_antimeridian,
])


__all__ = (
    "default_transformer",
    "fixed_size_polygon_crosses_antimeridian",
    "polygon_crosses_antimeridian",
    "reverse_polygon",
    "simplify_polygon",
    "split_polygon_on_antimeridian",
    "to_polygons",
    "Transformation",
    "TransformationResult",
    "Transformer",
)
