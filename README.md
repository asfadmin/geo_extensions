# Geo Extensions

This library consists of some common functions needed to manipulate polygons
before posting them to CMR. This includes functions to split polygons along
the antimeridian and perform other 'clean up' operations.


## Example Usage

Polygons are manipulated using a composable pipeline of transformation
functions. A transformation function is any function with the following
signature:

```python
def transformation(polygon: Polygon) -> Generator[Polygon]:
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
