from datetime import datetime
import pygame
from core import elements, font_helper, colors
import digitransit.routing

class StoptimeShortnameRenderer(elements.StoptimeBaseRenderer):
    def setup(self) -> None:
        self.font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Bold.ttf")

    def get_value(self, stoptime: digitransit.routing.Stoptime, current_time: datetime) -> str:
        assert stoptime.trip is not None
        assert stoptime.trip.route.shortName is not None

        return stoptime.trip.route.shortName

    def get_error_value(self) -> str:
        return "<e>"

    def get_rect(self) -> pygame.Rect:
        stoptime_rect: pygame.Rect = elements.position_params.get_stoptime_rect(self.stoptime_index)
        w: int = elements.position_params.stoptime_shortname_headsign_split_x - stoptime_rect.left

        return pygame.Rect(stoptime_rect.topleft, (w, stoptime_rect.height))

    def render(self, size: tuple[int, int], flags: elements.RenderFlags) -> pygame.Surface | None:
        surf = pygame.Surface(size, pygame.SRCALPHA)

        font_height: int = self.get_font_height(size[1])
        line_number_render = self.font.get_size(font_height).render(self.value, True, colors.Colors.WHITE)

        surf.blit(line_number_render, (0, size[1] // 2 - line_number_render.get_height() // 2))

        return surf
