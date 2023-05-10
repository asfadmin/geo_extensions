import pytest
from satlib import FlightDirection, LookDirection


def test_flight_direction_from_str():
    assert FlightDirection.from_str("A") == FlightDirection.ascending
    assert FlightDirection.from_str("ASC") == FlightDirection.ascending
    assert (
        FlightDirection.from_str("ascENDing", case_sensitive=False)
        == FlightDirection.ascending
    )

    assert FlightDirection.from_str("D") == FlightDirection.descending
    assert FlightDirection.from_str("DES") == FlightDirection.descending
    assert (
        FlightDirection.from_str("DEScendING", case_sensitive=False)
        == FlightDirection.descending
    )


def test_flight_direction_from_str_error():
    with pytest.raises(ValueError, match="Cannot determine FlightDirection"):
        FlightDirection.from_str("foobar")


def test_look_direction_from_str():
    assert LookDirection.from_str("R") == LookDirection.right
    assert LookDirection.from_str("RIG") == LookDirection.right
    assert LookDirection.from_str("rIghT", case_sensitive=False) == LookDirection.right

    assert LookDirection.from_str("L") == LookDirection.left
    assert LookDirection.from_str("LEF") == LookDirection.left
    assert LookDirection.from_str("LeFT", case_sensitive=False) == LookDirection.left


def test_look_direction_from_str_error():
    with pytest.raises(ValueError, match="Cannot determine LookDirection"):
        LookDirection.from_str("foobar")
