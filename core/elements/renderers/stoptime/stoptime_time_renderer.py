from datetime import datetime
import pygame
from core import elements, font_helper, colors
from digitransit.enums import RealtimeState
import digitransit.routing

CANCELLED_PREFIX: str = "!!CANCELLED_"

class StoptimeTimeRenderer(elements.StoptimeBaseRenderer):
    def setup(self) -> None:
        self.font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Bold.ttf")

    def get_value(self, stoptime: digitransit.routing.Stoptime, current_time: datetime) -> str:
        assert stoptime.realtimeDeparture is not None and stoptime.scheduledDeparture is not None
        departure: datetime = stoptime.realtimeDeparture if stoptime.realtime == True else stoptime.scheduledDeparture

        # Formatting
        departure_time_text: str
        if stoptime.realtime == True and stoptime.realtimeState not in (RealtimeState.SCHEDULED, RealtimeState.CANCELED):
            departure_diff = departure - current_time
            diff_minutes: int = round(departure_diff.total_seconds() / 60)
            diff_minutes = max(diff_minutes, 0)
            departure_time_text = str(diff_minutes)
        else:
            departure_time_text = departure.strftime(elements.TIMEFORMAT)

        # Cancelled
        if stoptime.realtimeState == RealtimeState.CANCELED:
            departure_time_text = CANCELLED_PREFIX + departure_time_text

        return departure_time_text

    def get_error_value(self) -> str:
        return "<error>"

    def get_rect(self) -> pygame.Rect:
        stoptime_rect: pygame.Rect = elements.position_params.get_stoptime_rect(self.stoptime_index)
        height: int = stoptime_rect.height

        x_calc_font = self.font.get_size(self.get_font_height(height))
        x: int = elements.position_params.get_stoptime_headsign_time_split_x(x_calc_font)

        w: int = stoptime_rect.right - x

        return pygame.Rect(x, stoptime_rect.top, w, height)

    def render(self, size: tuple[int, int], flags: elements.RenderFlags) -> pygame.Surface | None:
        cancelled: bool = False
        time_str: str = self.value
        if time_str.startswith(CANCELLED_PREFIX):
            cancelled = True
            time_str.removeprefix(CANCELLED_PREFIX)

        font_height: int = self.get_font_height(size[1])
        departure_time_render = self.font.get_size(font_height).render(time_str, True, colors.Colors.WHITE)

        # render strikethrough if canceled.
        if cancelled:
            departure_time_size = departure_time_render.get_size()
            strikethrough_y = round(departure_time_size[1] / 2)
            strikethrough_thickness = max(round(departure_time_size[1] / 14), 1)
            pygame.draw.line(
                departure_time_render, colors.Colors.WHITE,
                (0, strikethrough_y), (departure_time_size[0], strikethrough_y),
                strikethrough_thickness
            )
        #endregion

        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.blit(departure_time_render, (size[0] - departure_time_render.get_width(), size[1] // 2 - departure_time_render.get_height() // 2))

        return surf
