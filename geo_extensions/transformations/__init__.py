"""Geospatial helpers to prepare spatial extents for submission to CMR.

CMR can interpret polygons as being in one of two coordinate systems, Cartesian
or Geodetic. Transformation helpers that must assume they are working in one of
these two coordinate systems all found in their own submodules `cartesian` and
`geodetic`.

Each coordinate system also has its own set of constraints that polygons must
follow. These constraints are documented in the corresponding module for the
coordinate system.

There are some additional constraints that depend on the data format being used.
For UMM-G, polygons must
    - Be counter clockwise ordered
    - Include closure points

In this module, polygons are expected to follow the UMM-G constraints.

A table describing the differences between data format requirements can be found
here:
https://wiki.earthdata.nasa.gov/display/CMR/Polygon+Support+in+CMR+Search+and+Ingest+Interfaces

There are several challenges with representing polygons on a spherical surface,
the primary being that since all straight lines will 'wrap around' the surface,
it becomes impossible to unabmiguously define a polygon using only an ordered
set of points. This is the primary reason for the CMR requirements, as those
additional constraints make it possible to determine exactly which area is
meant by a set of points. Unfortunately, the polygons that we get from the data
provider won't necessarily meet those same requirements and we must use mission
specific knowledge to convert them to an unambiguous set of polygons to be used
by CMR.

This module aims to assist in that conversion to unambiguous polygons using the
CMR additional requirements.
"""

from geo_extensions.transformations.cartesian import (
    simplify_polygon,
    split_polygon_on_antimeridian_ccw,
    split_polygon_on_antimeridian_fixed_size,
)
from geo_extensions.transformations.general import drop_z_coordinate, reverse_polygon
from geo_extensions.transformations.geodetic import densify_polygon

__all__ = (
    "densify_polygon",
    "drop_z_coordinate",
    "reverse_polygon",
    "simplify_polygon",
    "split_polygon_on_antimeridian_ccw",
    "split_polygon_on_antimeridian_fixed_size",
)
