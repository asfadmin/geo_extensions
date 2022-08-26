from typing import Tuple


def center_lat_to_esa_frame(center_lat: float, ascending: bool) -> int:
    """Convert a latitude value and flight direction to ESA frame number"""
    assert -90.0 <= center_lat <= 90.0, "invalid latitude value"

    if not ascending:
        center_lat = 180 - center_lat

    return int(center_lat * 20 % 7200)


def esa_frame_to_center_lat(frame: int) -> Tuple[float, bool]:
    """Convert a ESA frame number to latitude value and flight direction"""
    assert 0 <= frame < 7200, "invalid frame value"

    lat = frame / 20

    if lat > 270:
        lat -= 360
        return lat, True
    if lat > 90:
        lat = 180 - lat
        return lat, False

    return lat, True
