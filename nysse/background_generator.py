from core.colors import NysseColors
import pygame
import pygame.gfxdraw
import math

def generateBackground(px_size: tuple[int, int]):
    surf = pygame.Surface(px_size)
    surf.fill(NysseColors.KESKISININEN)

    sine_rect = pygame.Rect(0, 0, (px_size[0] / 6) * 5.35, (px_size[0] / 6) * 5.35)
    sine_length: int = 1 + math.ceil(math.hypot(sine_rect.width, sine_rect.height))

    # Frequency matches asemanäyttö, not design guidelines
    sine_freq: float = 19.6452 / sine_rect.width
    sine_amp = 0.0155 * sine_rect.height

    points: list[tuple[float, float]] = []
    for iter_x in range(0, round(sine_length * 1.1), 1): # Added some extra x points to fix sine not being long enough
        p = _generateSine(iter_x, sine_freq, sine_amp)
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


def _generateSine(x: float, wave_frequency: float, wave_amplitude: float) -> tuple[float, float]:
    y = wave_amplitude * -math.cos(wave_frequency * x)
    return (x, y)

def _rotatePoint(origin: tuple[float, float], point: tuple[float, float], angle: float) -> tuple[float, float]:
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
