from core.colors import Colors
import datetime
from typing import Optional, Tuple
import pygame
import pygame.font
import pygame.surface

font: Optional[pygame.font.Font] = None
font_height: Optional[int] = None

TIMEFORMAT = "%H:%M"

def renderTime(px_height: int, time: datetime.time = None, color: Tuple[int, int, int] = Colors.WHITE) -> pygame.surface.Surface:
    global font, font_height
    if font == None or font_height != px_height:
        print("Loading new font for time rendering...")
        font = pygame.font.Font("resources/fonts/Lato-Bold.ttf", px_height)
        font_height = px_height
    if time == None:
        time = datetime.datetime.now().time()

    timeStr = time.strftime(TIMEFORMAT)
    return font.render(timeStr, True, color)
