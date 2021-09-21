from core.colors import NysseColors
import pygame
import math
from typing import Tuple

def generateBackground(px_size: Tuple[int, int], wave_count: int = 3):
    surf = pygame.Surface(px_size)
    surf.fill(NysseColors.KESKISININEN)


def getWavePoints(count: int, x: float, width: float):
    pass

_easeInOutSine = lambda x: -(math.cos(math.pi * x) - 1) / 2

def getWavePoint(t: float, width: float) -> Tuple[float, float]:
    yt = _easeInOutSine(t % 0.5)
    if t > 0.5:
        yt = 1 - yt

    x: float = t * width
    y: float = yt * (width / 2)

    return (x, y)
