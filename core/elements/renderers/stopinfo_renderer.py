import pygame
from core import elements, font_helper
from core.colors import Colors

class StopInfoRenderer(elements.ElementRenderer):
    def __init__(self) -> None:
        self.stopname: str = "<error>"

    def setup(self) -> None:
        self.unscaled_stop_icon = pygame.image.load("resources/textures/icons/pysakki.png").convert_alpha()
        self.font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Bold.ttf", purpose="stop info rendering")

    def update(self, context: elements.UpdateContext) -> bool:
        changes: bool = False

        new_stopname: str = context.stopinfo.name
        if self.stopname != new_stopname:
            self.stopname = new_stopname
            changes = True

        return changes

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        return params.stop_info_rect

    def render(self, size: tuple[int, int]) -> pygame.Surface | None:
        font_height: int = size[1] - round(size[1] / 3)

        icon_size: int = round(size[1] / 1.75)
        stop_icon = pygame.transform.smoothscale(self.unscaled_stop_icon, (icon_size, icon_size))

        surf = pygame.Surface(size, pygame.SRCALPHA)
        # DEBUG: surf.fill(Colors.RED)

        stopnamernd = self.font.get_size(font_height).render(self.stopname, True, Colors.WHITE)
        surf.blit(stopnamernd, (0, size[1] // 2 - stopnamernd.get_height() // 2))
        surf.blit(stop_icon, (size[0] - stop_icon.get_width(), size[1] // 2 - stop_icon.get_height() // 2))

        line_thickness = max(size[1] // 40, 1)
        pygame.draw.line(surf, Colors.WHITE, (0, line_thickness // 2), (size[0], line_thickness // 2), width=line_thickness)
        pygame.draw.line(surf, Colors.WHITE, (0, size[1] - line_thickness), (size[0], size[1] - line_thickness), width=line_thickness)

        return surf
