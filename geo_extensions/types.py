from collections.abc import Callable, Generator

from shapely.geometry import Polygon

TransformationResult = Generator[Polygon]
Transformation = Callable[[Polygon], TransformationResult]
