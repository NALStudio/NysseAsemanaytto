from datetime import datetime
import pygame
from core import elements, font_helper, colors
import digitransit.routing

class StoptimeHeadsignRenderer(elements.StoptimeBaseRenderer):
    def __init__(self, stoptime_index: int, shortname_renderer: elements.StoptimeShortnameRenderer, time_renderer: elements.StoptimeTimeRenderer) -> None:
        super().__init__(stoptime_index)
        self.shortname_renderer: elements.StoptimeShortnameRenderer = shortname_renderer
        self.time_renderer: elements.StoptimeTimeRenderer = time_renderer

    def setup(self) -> None:
        self.font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Regular.ttf")

    def get_value(self, stoptime: digitransit.routing.Stoptime, current_time: datetime) -> str:
        assert stoptime.headsign is not None
        return stoptime.headsign

    def get_error_value(self) -> str:
        return "<error>"

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        stoptime_rect: pygame.Rect = params.get_stoptime_rect(self.stoptime_index)
        height: int = stoptime_rect.height

        left: int = params.stoptime_shortname_headsign_split_x

        right_calc_font = self.time_renderer.font.get_size(self.get_font_height(height))
        right: int = params.get_stoptime_headsign_time_split_x(right_calc_font)

        width: int = right - left

        return pygame.Rect(left, stoptime_rect.top, width, height)

    def render(self, size: tuple[int, int]) -> pygame.Surface | None:
        font_height: int = self.get_font_height(size[1])
        line_headsign_render = self.font.get_size(round(font_height * 0.9)).render(self.value, True, colors.Colors.WHITE)

        surf = pygame.Surface(size, pygame.SRCALPHA)

        line_number_height: int = self.shortname_renderer.font.get_size(font_height).get_height()
        surf.blit(line_headsign_render, (0, size[1] // 2 + line_number_height // 2 - line_headsign_render.get_height()))

        return surf
