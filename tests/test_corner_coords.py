from satlib import FlightDirection, LookDirection
from satlib.corner_coords import CornerCoords


def test_from_ub_ascending_right():
    upper_left, upper_right, bottom_left, bottom_right = (1, 2), (3, 4), (5, 6), (7, 8)
    coords = CornerCoords.from_ub(
        upper_left,
        upper_right,
        bottom_left,
        bottom_right,
        FlightDirection.ascending,
        LookDirection.right
    )

    assert coords == CornerCoords(bottom_left, upper_left, bottom_right, upper_right)


def test_from_ub_ascending_left():
    upper_left, upper_right, bottom_left, bottom_right = (1, 2), (3, 4), (5, 6), (7, 8)
    coords = CornerCoords.from_ub(
        upper_left,
        upper_right,
        bottom_left,
        bottom_right,
        FlightDirection.ascending,
        LookDirection.left
    )

    assert coords == CornerCoords(bottom_right, upper_right, bottom_left, upper_left)


def test_from_ub_descending_right():
    upper_left, upper_right, bottom_left, bottom_right = (1, 2), (3, 4), (5, 6), (7, 8)
    coords = CornerCoords.from_ub(
        upper_left,
        upper_right,
        bottom_left,
        bottom_right,
        FlightDirection.descending,
        LookDirection.right
    )

    assert coords == CornerCoords(upper_right, bottom_right, upper_left, bottom_left)


def test_from_ub_descending_left():
    upper_left, upper_right, bottom_left, bottom_right = (1, 2), (3, 4), (5, 6), (7, 8)
    coords = CornerCoords.from_ub(
        upper_left,
        upper_right,
        bottom_left,
        bottom_right,
        FlightDirection.descending,
        LookDirection.left
    )

    assert coords == CornerCoords(upper_left, bottom_left, upper_right, bottom_right)
