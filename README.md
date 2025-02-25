# Geo Extensions

This library consists of some common functions needed to manipulate polygons
before posting them to CMR. This includes functions to split polygons along
the antimeridian and perform other 'clean up' operations.


## Example Usage

Polygons are manipulated using a composable pipeline of transformation
functions. A transformation function is any function with the following
signature:

```python
def transformation(polygon: Polygon) -> Generator[Polygon, None, None]:
    ...
```

A Transformer object is created with a list of transformations, and then can
be reused to perform the same manipulation on many polygons.

```python
from geo_extensions import Transformer
from geo_extensions.transformations import (
    simplify_polygon,
    split_polygon_on_antimeridian_ccw,
)


def my_custom_transformation(polygon):
    """Duplicate polygon"""

    yield polygon
    yield polygon


transformer = Transformer([
    simplify_polygon(0.1),
    my_custom_transformation,
    split_polygon_on_antimeridian_ccw,
])

final_polygons = transformer.transform([
    Polygon([
        (150., 10.), (150., -10.),
        (-150., -10.), (-150., 10.), (150., 10.),
    ])
])
```

The default transformer performs some standard transformations that are usually
needed. Check the definition for what those transformations are.

```python
from geo_extensions import default_transformer


WKT = "MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), ((15 5, 40 10, 10 20, 5 10, 15 5)))"

polygons = default_transformer.from_wkt(WKT)
```
