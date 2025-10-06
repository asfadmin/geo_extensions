# Geo Extensions

This library consists of some common functions needed to manipulate polygons
before posting them to CMR. This includes functions to split polygons along
the antimeridian and perform other 'clean up' operations.

## Beware the Coordinate System

CMR supports two modes for interpreting how the points of a polygon are supposed
to be connected to each other: Geodetic and Cartesian.

In the geodetic coordinate system, points are connected to each other by the
shortest arc on a  spherical approximation of the Earth. This is the closest
system to how a  satellite would actually be seeing the area in the real world.
However, it is not typically the way that polygons would be rendered in a web
search tool as these usually use web mercator projection.

In the cartesian coordinate system, points are connected to each other more or
less along longitude and latitude lines. This means that points will be
connected by straight lines when viewed in a mercator projection, which is
useful for web tools but not necessarily an accurate representation of the data
acquired by the satellite.

Keep these differences in mind when implementing a polygon transformation
pipeline, and be aware of what mode the collection you are posting to is set up
in. As a general rule, the higher the point density is on a polygon, the less
the difference between the two coordinate system interpretations will be because
each line segment will be shorter. It is therefore a good idea to start your
pipeline with a 'densify' operation, do the desired transformations, and then
simplify at the end.

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
    my_custom_transformation,
    split_polygon_on_antimeridian_ccw,
    simplify_polygon(0.1),
])

final_polygons = transformer.transform([
    Polygon([
        (150., 10.), (150., -10.),
        (-150., -10.), (-150., 10.), (150., 10.),
    ])
])
```
