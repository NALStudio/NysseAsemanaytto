from core.colors import Colors
import datetime
import pygame
import pygame.font
import pygame.surface

font: pygame.font.Font | None = None
font_height: int | None = None

TIMEFORMAT = "%H:%M"

def renderTime(px_height: int, time: datetime.time | None = None, color: tuple[int, int, int] = Colors.WHITE) -> pygame.surface.Surface:
    global font, font_height
    if font is None or font_height != px_height:
        print("Loading new font for time rendering...")
        font = pygame.font.Font("resources/fonts/Lato-Bold.ttf", px_height)
        font_height = px_height
    if time is None:
        time = datetime.datetime.now().time()

    timeStr = time.strftime(TIMEFORMAT)
    return font.render(timeStr, True, color)
