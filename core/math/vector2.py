from __future__ import annotations

from typing import NamedTuple

from core import math


class Vector2(NamedTuple):
    """An immutable two-dimensional vector"""

    x: float
    y: float


    @classmethod
    @property
    def zero(cls) -> math.Vector2:
        """Shorthand for ``math.Vector2(0.0, 0.0)``"""
        return _ZERO #  Returning single instance, because Vector2 is immutable

    @classmethod
    @property
    def one(cls) -> math.Vector2:
        """Shorthand for ``math.Vector2(1.0, 1.0)``"""
        return _ONE #  Returning single instance, because Vector2 is immutable


    def __str__(self) -> str:
        """Human-readable string representation of the vector."""
        return f"Vector2({self.x}, {self.y})"

    def __repr__(self) -> str:
        """Unambiguous string representation of the vector."""
        return repr((self.x, self.y))

    def __add__(self, other: Vector2) -> Vector2:
        """Add"""
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        """Subtract"""
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: Vector2 | float | int) -> Vector2:
        """Multiply"""
        x: float
        y: float
        if isinstance(other, Vector2):
            x = other.x
            y = other.y
        else:
            x = other
            y = other

        return Vector2(self.x * x, self.y * y)

    def __truediv__(self, other: Vector2 | float | int) -> Vector2:
        """Divide"""
        x: float
        y: float
        if isinstance(other, Vector2):
            x = other.x
            y = other.y
        else:
            x = other
            y = other

        return Vector2(self.x / x, self.y / y)

    def __neg__(self) -> Vector2:
        """Negate"""
        return Vector2(-self.x, -self.y)

    def __abs__(self) -> Vector2:
        return Vector2(abs(self.x), abs(self.y))

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Vector2) and __o.x == self.x and __o.y == self.y


    @property
    def magnitude(self) -> float:
        return math.hypot(self.x, self.y)

    @property
    def sqr_magnitude(self) -> float:
        return (self.x * self.x) + (self.y * self.y)

    @property
    def normalized(self):
        mag: float = self.magnitude
        return Vector2(self.x / mag, self.y / mag)


    @staticmethod
    def lerp(a: Vector2, b: Vector2, t: float) -> Vector2:
        t = math.clamp01(t)
        lerp_x = a.x + ((b.x - a.x) * t)
        lerp_y = a.y + ((b.y - a.y) * t)
        return Vector2(lerp_x, lerp_y)

    @staticmethod
    def lerp_unclamped(a: Vector2, b: Vector2, t: float) -> Vector2:
        lerp_x = a.x + ((b.x - a.x) * t)
        lerp_y = a.y + ((b.y - a.y) * t)
        return Vector2(lerp_x, lerp_y)

    @staticmethod
    def move_towards(current: Vector2, target: Vector2, max_distance_delta: float):
        to_vector_x: float = target.x - current.x
        to_vector_y: float = target.y - current.y

        sqDist: float = to_vector_x * to_vector_x + to_vector_y * to_vector_y

        if sqDist == 0 or (max_distance_delta >= 0 and sqDist <= max_distance_delta * max_distance_delta):
            return target

        dist: float = math.sqrt(sqDist)

        move_x = current.x + to_vector_x / dist * max_distance_delta
        move_y = current.y + to_vector_y / dist * max_distance_delta
        return Vector2(move_x, move_y)

    @staticmethod
    def angle(_from: Vector2, _to: Vector2):
        diff = _to - _from
        return math.degrees(math.atan2(diff.y, diff.x))

    @staticmethod
    def distance(a: Vector2, b: Vector2):
        diff = a - b
        return diff.magnitude


    def to_float_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    def to_int_tuple(self) -> tuple[int, int]:
        return (round(self.x), round(self.y))

    def to_int_list(self) -> list[int]:
        return [round(self.x), round(self.y)]


_ZERO = Vector2(0.0, 0.0)
_ONE = Vector2(1.0, 1.0)
