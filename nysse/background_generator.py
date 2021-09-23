from core.colors import NysseColors
import pygame
import pygame.gfxdraw
import math
from typing import List, Tuple

FREQUENCY: float = 0.03825 # TODO: Make them scale with screen size
AMPLITUDE: float = 8.0

def generateBackground(px_size: Tuple[int, int]):
    surf = pygame.Surface(px_size)
    surf.fill(NysseColors.KESKISININEN)

    sine_rect = pygame.Rect(0, 0, (px_size[0] / 6) * 5.35, (px_size[0] / 6) * 5.35)
    sine_length: int = 1 + math.ceil(math.hypot(sine_rect.width, sine_rect.height))

    points: List[Tuple[float, float]] = []
    for iter_x in range(0, round(sine_length * 1.1), 1): # Added some extra x points to fix sine not being long enough
        p = _generateSine(iter_x, FREQUENCY, AMPLITUDE)
        points.append(p)

    # Transform points
    for i in range(len(points)):
        x, y = points[i]

        x -= (sine_length - sine_rect.width) / 2
        y += sine_rect.height / 2

        x, y = _rotatePoint((sine_rect.centerx, sine_rect.centery), (x, y), math.radians(-45.0))

        points[i] = (x, y)


    points.insert(0, (0, 0))
    points.append((0, 0))

    pygame.gfxdraw.filled_polygon(surf, points, NysseColors.TUMMANSININEN)

    return surf


def _generateSine(x: float, wave_frequency: float, wave_amplitude: float) -> Tuple[float, float]:
    y = wave_amplitude * -math.cos(wave_frequency * x)
    return (x, y)

def _rotatePoint(origin: Tuple[float, float], point: Tuple[float, float], angle: float) -> Tuple[float, float]:
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    angleSin = math.sin(angle)
    angleCos = math.cos(angle)

    x_diff = px - ox
    y_diff = py - oy

    qx = ox + angleCos * x_diff - angleSin * y_diff
    qy = oy + angleSin * x_diff + angleCos * y_diff

    return (qx, qy)