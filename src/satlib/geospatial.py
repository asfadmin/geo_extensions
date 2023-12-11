import logging
from typing import List, Tuple

from shapely.geometry import LineString, Polygon
from shapely.ops import linemerge, polygonize, unary_union

Point = Tuple[float, float]
Bbox = List[Point]

ANTIMERIDIAN = LineString([(180, 90), (180, -90)])


def bbox_to_polygon(bbox: Bbox) -> Polygon:
    return Polygon([(lon, lat) for lat, lon in bbox])


def polygon_to_bbox(polygon: Polygon) -> Bbox:
    return [(lat, lon) for lon, lat in polygon.boundary.coords]


def split_bbox_on_idl(
    bbox: Bbox,
    include_closure_points: bool = False,
    ccw: bool = False
) -> List[Bbox]:
    """Perform adjustment when the bounding box crosses the 180 longitude line.

    CMR requires the bounding box to be split into two separate bounding bboxes
    to avoid the polygon being interpreted as wrapping the long way around the
    Earth.

    DEPRECATED: Use split_polygon_on_idl instead.

    :param bbox: the bounding box to split if necessary
    :param include_closure_points: whether or not to include the closure point
        in the returned bounding boxes
    :param ccw: whether or not to use counter clockwise winding order
    """
    new_polygons = split_polygon_on_idl(polygon=bbox_to_polygon(bbox))
    new_bboxes = []
    # Shift back to -180-180 range
    for new_polygon in new_polygons:
        new_bbox = polygon_to_bbox(new_polygon)
        if ccw:
            new_bbox = new_bbox[::-1]

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


def split_polygon_on_idl(polygon: Polygon) -> List[Polygon]:
    """Perform adjustment when the polygon crosses the 180 longitude line.

    CMR requires the polygon to be split into two separate polygons to avoid it
    being interpreted as wrapping the long way around the Earth.

    :param polygon: the polygon to split if necessary
    """

    shifted_polygon = _shift_polygon(polygon)
    if not shifted_polygon.intersects(ANTIMERIDIAN):
        return [polygon]

    new_polygons = _split_polygon(shifted_polygon, ANTIMERIDIAN)

    return [
        _shift_polygon_back(polygon)
        for polygon in new_polygons
    ]


def _shift_polygon(polygon: Polygon) -> Polygon:
    """Shift into 0-360 range."""

    return Polygon([
        ((360.0 + lon) % 360, lat)
        for lon, lat in polygon.boundary.coords
    ])


def _shift_polygon_back(polygon: Polygon) -> Polygon:
    """Shift back to -180-180 range.

    Also replaces points that land right on +/-180 with +/-179.999.
    """

    _, _, max_lon, _ = polygon.bounds
    return Polygon([
        (_adjust_lon(lon, max_lon), lat)
        for lon, lat in polygon.boundary.coords
    ])


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


def _split_polygon(
    polygon: Polygon,
    line: LineString
) -> List[Polygon]:
    """Polygon and line must intersect."""

    merged = linemerge([polygon.boundary, line])
    borders = unary_union(merged)
    return polygonize(borders)
