from typing import Callable, Generator

from shapely.geometry import Polygon

TransformationResult = Generator[Polygon, None, None]
Transformation = Callable[[Polygon], TransformationResult]
