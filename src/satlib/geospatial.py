import logging
from typing import List

from shapely.geometry import LineString, Polygon
from shapely.ops import linemerge, polygonize, unary_union

Point = List[float]
Bbox = List[Point]

ANTIMERIDIAN = LineString([(180, 90), (180, -90)])


def _adjust_lon(lon: float, max_lon: float) -> float:
    if lon > 180.0:
        return lon - 360
    elif lon == 180.0 and max_lon == 180.0:
        return 179.999
    elif lon == 180.0:
        return -179.999

    return lon


def _has_closure_point(bbox: Bbox) -> bool:
    assert len(bbox) >= 2

    return bbox[0] == bbox[-1]


def split_bbox_on_idl(bbox: Bbox, include_closure_points: bool = False):
    """Perform adjustment when the bounding box crosses the 180 longitude line.

    CMR requires the bounding box to be split into two separate bounding bboxes
    to avoid the polygon being interpreted as wrapping the long way around the
    Earth.
    """
    # Shift into 0-360 range
    shifted_polygon = Polygon([((360.0 + lon) % 360, lat) for lat, lon in bbox])
    if not shifted_polygon.intersects(ANTIMERIDIAN):
        return [bbox]
    merged = linemerge([shifted_polygon.boundary, ANTIMERIDIAN])
    borders = unary_union(merged)
    polygons = polygonize(borders)

    # Shift back to -180-180 range
    new_bboxes = []
    for p in polygons:
        new_bbox = [[lat, lon] for lon, lat in p.boundary.coords]
        max_lon = max(lon for lat, lon in new_bbox)
        new_bbox = [[lat, _adjust_lon(lon, max_lon)] for lat, lon in new_bbox]

        if _has_closure_point(bbox):
            # UMM-G requires closure points to be present, however our old code
            # had a comment saying that CMR did not want the closure point.
            # Maybe it depends on the format you use to post to CMR?
            if include_closure_points:
                new_bboxes.append(new_bbox)
            else:
                new_bboxes.append(new_bbox[:-1])
        else:
            logging.debug("IDL crossing splinter is being ignored")
            # TODO(reweeden): How does this happen? Add a test case
            raise RuntimeError("Test me!", bbox)

    return new_bboxes
