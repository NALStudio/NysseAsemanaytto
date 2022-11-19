from datetime import time
import pygame
from core import elements, font_helper
from core.colors import Colors

class HeaderTimeRenderer(elements.ElementRenderer):
    def __init__(self) -> None:
        self.time: time = time()

    def setup(self) -> None:
        self.font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Bold.ttf", "time rendering")

    def update(self, context: elements.UpdateContext) -> bool:
        changes: bool = False

        time = context.time

        if self.time.hour != time.hour:
            self.time = self.time.replace(hour=time.hour)
            changes = True

        if self.time.minute != time.minute:
            self.time = self.time.replace(minute=time.minute)
            changes = True

        return changes

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        header_rect: pygame.Rect = params.header_rect

        w: int = header_rect.height * 3 # *3 should be enough to contain the time render
        h: int = header_rect.height

        x: int = header_rect.right - w
        y: int = header_rect.top

        return pygame.Rect(x, y, w, h)

    def render(self, size: tuple[int, int]) -> pygame.Surface | None:
        time_str: str = self.time.strftime(elements.TIMEFORMAT)
        time: pygame.Surface = self.font.get_size(size[1]).render(time_str, True, Colors.WHITE)

        surf: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
        surf.blit(time, (size[0] - time.get_width(), size[1] - time.get_height())) # Height aligned from bottom because font has whitespace above each letter

        return surf
