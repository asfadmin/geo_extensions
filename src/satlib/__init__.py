from enum import Enum
from typing import Iterable


class FromStrMixin:
    @classmethod
    def from_str(cls: Iterable[Enum], value: str, case_sensitive: bool = True):
        if not case_sensitive:
            value = value.upper()
        for variant in cls:
            variant_value = variant.value if case_sensitive else variant.value.upper()
            if variant_value.startswith(value):
                return variant

        raise ValueError(f"Cannot determine {cls.__name__} from string {value!r}")


class FlightDirection(FromStrMixin, Enum):
    ascending = "ASCENDING"
    descending = "DESCENDING"


class LookDirection(FromStrMixin, Enum):
    right = "RIGHT"
    left = "LEFT"
