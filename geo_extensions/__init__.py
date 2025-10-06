from geo_extensions.checks import (
    polygon_crosses_antimeridian_ccw,
    polygon_crosses_antimeridian_fixed_size,
)
from geo_extensions.transformations import (
    densify_polygon,
    drop_z_coordinate,
    reverse_polygon,
    simplify_polygon,
    split_polygon_on_antimeridian_ccw,
    split_polygon_on_antimeridian_fixed_size,
)
from geo_extensions.transformer import Transformer, to_polygons
from geo_extensions.types import Transformation, TransformationResult

default_transformer = Transformer([
    simplify_polygon(0.1),
    split_polygon_on_antimeridian_ccw,
])


__all__ = (
    "default_transformer",
    "densify_polygon",
    "drop_z_coordinate",
    "polygon_crosses_antimeridian_ccw",
    "polygon_crosses_antimeridian_fixed_size",
    "reverse_polygon",
    "simplify_polygon",
    "split_polygon_on_antimeridian_ccw",
    "split_polygon_on_antimeridian_fixed_size",
    "to_polygons",
    "Transformation",
    "TransformationResult",
    "Transformer",
)
