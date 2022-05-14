from __future__ import annotations

from typing import NamedTuple

import pygame
from core import math


class Rect(NamedTuple):
    position: math.Vector2
    size: math.Vector2

    @classmethod
    def from_corners(cls, topleft: math.Vector2, bottomright: math.Vector2):
        size = bottomright - topleft
        return cls(topleft, size)

    @classmethod
    def from_sides(cls, left: float, top: float, right: float, bottom: float):
        topleft = math.Vector2(left, top)
        size = math.Vector2(right - left, bottom - top)
        return cls(topleft, size)

    @classmethod
    def from_center(cls, center: math.Vector2, size: math.Vector2):
        topleft = center - (size / 2.0)
        return cls(topleft, size)

    @property
    def x(self) -> float:
        return self.position.x

    @property
    def y(self) -> float:
        return self.position.y

    @property
    def w(self) -> float:
        return self.size.x

    @property
    def h(self) -> float:
        return self.size.y

    @property
    def left(self) -> float:
        return self.position.x

    @property
    def right(self) -> float:
        return self.position.x + self.size.x

    @property
    def top(self) -> float:
        return self.position.y

    @property
    def bottom(self) -> float:
        return self.position.y + self.size.y

    @property
    def topleft(self) -> math.Vector2:
        return math.Vector2(self.left, self.top)

    @property
    def bottomleft(self) -> math.Vector2:
        return math.Vector2(self.left, self.bottom)

    @property
    def topright(self) -> math.Vector2:
        return math.Vector2(self.right, self.top)

    @property
    def bottomright(self) -> math.Vector2:
        return math.Vector2(self.right, self.bottom)

    @property
    def midtop(self) -> math.Vector2:
        return math.Vector2(self.center_x, self.top)

    @property
    def midbottom(self) -> math.Vector2:
        return math.Vector2(self.center_x, self.bottom)

    @property
    def midleft(self) -> math.Vector2:
        return math.Vector2(self.left, self.center_y)

    @property
    def midright(self) -> math.Vector2:
        return math.Vector2(self.right, self.center_y)

    @property
    def center_y(self) -> float:
        return self.position.y + (self.size.y / 2.0)

    @property
    def center_x(self) -> float:
        return self.position.x + (self.size.x / 2.0)

    @property
    def center(self) -> math.Vector2:
        return math.Vector2(self.center_x, self.center_y)

    def collide_point(self, point: math.Vector2) -> bool:
        """Checks whether a point lies within the borders of this rect."""
        return (self.left < point.x < self.right
                and self.top < point.y < self.bottom)  # nopep8

    def collide_rect(self, rect: Rect) -> bool:
        """Checks whether another rect overlaps with the borders of this rect."""
        # If any of the checks fail the rectangles don't overlap
        return (not (self.right < rect.left)
                and not (self.left > rect.right)   # noqa: W503
                and not (self.top > rect.bottom)   # noqa: W503
                and not (self.bottom < rect.top))  # noqa: W503

    def to_float_tuple(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.w, self.h)

    def to_int_tuple(self) -> tuple[int, int, int, int]:
        x = round(self.x)
        y = round(self.y)
        w = round(self.w)
        h = round(self.h)
        return (x, y, w, h)

    def to_pygame_rect(self) -> pygame.Rect:
        return pygame.Rect(*self.to_int_tuple())
