from digitransit.routing import Stop
from core.colors import Colors
from core import font_helper, logging
import pygame

font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Bold.ttf", "stop info rendering")

stop_icon: pygame.Surface | None = None

def render_stopinfo(px_size: tuple[int, int], stopinfo: Stop) -> pygame.Surface:
    global font, stop_icon
    font_height: int = px_size[1] - round(px_size[1] / 3)

    target_icon_size: int = round(px_size[1] / 1.75)
    if stop_icon is None or stop_icon.get_height() != target_icon_size:
        logging.debug("Loading new icon for stop info rendering...", stack_info=False)
        stop_icon = pygame.image.load("resources/textures/icons/pysakki.png")
        stop_icon = pygame.transform.smoothscale(stop_icon, (target_icon_size, target_icon_size)).convert_alpha()

    surf = pygame.Surface(px_size, pygame.SRCALPHA)
    # DEBUG: surf.fill(Colors.RED)

    stopnamernd = font.get_size(font_height).render(stopinfo.name, True, Colors.WHITE)
    surf.blit(stopnamernd, (0, px_size[1] // 2 - stopnamernd.get_height() // 2))
    surf.blit(stop_icon, (px_size[0] - stop_icon.get_width(), px_size[1] // 2 - stop_icon.get_height() // 2))

    line_thickness = max(px_size[1] // 40, 1)
    pygame.draw.line(surf, Colors.WHITE, (0, line_thickness // 2), (px_size[0], line_thickness // 2), width=line_thickness)
    pygame.draw.line(surf, Colors.WHITE, (0, px_size[1] - line_thickness), (px_size[0], px_size[1] - line_thickness), width=line_thickness)

    return surf
