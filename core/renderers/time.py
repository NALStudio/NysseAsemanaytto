from core.colors import Colors
from core import font_helper
import datetime
import pygame
import pygame.font
import pygame.surface

font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Bold.ttf", "time rendering")

TIMEFORMAT = "%H:%M"

def render_time(px_height: int, time: datetime.time | None = None, color: tuple[int, int, int] = Colors.WHITE) -> pygame.surface.Surface:
    global font, font_height
    if time is None:
        time = datetime.datetime.now().time()

    timeStr = time.strftime(TIMEFORMAT)
    return font.get_size(px_height).render(timeStr, True, color)
