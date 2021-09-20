from digitransit.routing import Stop
from typing import Optional, Tuple
from core.colors import Colors
import pygame
import pygame.draw
import pygame.font
import pygame.image
import pygame.surface
import pygame.transform

font: Optional[pygame.font.Font] = None
font_height: Optional[int] = None

stop_icon: Optional[pygame.surface.Surface] = None

def renderStopInfo(px_size: Tuple[int, int], stopinfo: Stop) -> pygame.Surface:
    global font, font_height, stop_icon
    target_font_height: int = px_size[1] - round(px_size[1] / 3)
    if font == None or target_font_height != font_height:
        print("Loading new font for stop info rendering...")
        font_height = target_font_height
        font = pygame.font.Font("resources/fonts/Lato-Bold.ttf", font_height)

    if stop_icon == None:
        print("Loading new icon for stop info rendering...")
        stop_icon = pygame.image.load("resources/textures/pictograms/pysakki.png")
        icon_size: int = round(px_size[1] / 1.75)
        stop_icon = pygame.transform.smoothscale(stop_icon, (icon_size, icon_size)).convert_alpha()

    surf = pygame.Surface(px_size)
    # DEBUG: surf.fill(Colors.RED)

    stopnamernd = font.render(stopinfo.name, True, Colors.WHITE)
    surf.blit(stopnamernd, (0, px_size[1] // 2 - stopnamernd.get_height() // 2))
    surf.blit(stop_icon, (px_size[0] - stop_icon.get_width(), px_size[1] // 2 - stop_icon.get_height() // 2))

    # ADJUST LINE THICKNESS IF THEY DO NOT RENDER
    line_thickness = px_size[1] // 40
    pygame.draw.line(surf, Colors.WHITE, (0, line_thickness // 2), (px_size[0], line_thickness // 2), width=line_thickness)
    pygame.draw.line(surf, Colors.WHITE, (0, px_size[1] - line_thickness), (px_size[0], px_size[1] - line_thickness), width=line_thickness)

    return surf