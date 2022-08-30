from typing import NamedTuple, Tuple

from satlib import FlightDirection, LookDirection


class CornerCoords(NamedTuple):
    """A container for converting corner coordinates to different reference
    systems.
    """

    near_start: Tuple[float, float]
    near_end: Tuple[float, float]
    far_start: Tuple[float, float]
    far_end: Tuple[float, float]

    @classmethod
    def from_ub(
        cls,
        upper_left: Tuple[float, float],
        upper_right: Tuple[float, float],
        bottom_left: Tuple[float, float],
        bottom_right: Tuple[float, float],
        flight_direction: FlightDirection,
        look_direction: LookDirection
    ):
        """Create corner coords from upper/bottom."""

        is_ascending = flight_direction is FlightDirection.ascending
        is_left = look_direction is LookDirection.left

        if is_ascending:
            start = (bottom_left, bottom_right)
            end = (upper_left, upper_right)
        else:
            start = (upper_right, upper_left)
            end = (bottom_right, bottom_left)

        if is_left:
            start = start[::-1]
            end = end[::-1]

        near_start, far_start = start
        near_end, far_end = end
        return cls(near_start, near_end, far_start, far_end)
