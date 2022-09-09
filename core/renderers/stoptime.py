from digitransit.enums import RealtimeState
from core.colors import Colors
from core import font_helper
import pygame
import core.renderers.time
import pygame.font
import datetime
from digitransit.routing import Stoptime

font_bold: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Bold.ttf")
font_regular: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Regular.ttf")

def render_stoptime(px_size: tuple[int, int], stoptime: Stoptime) -> pygame.Surface:
    font_height: int = px_size[1] - round(px_size[1] / 3)

    surf = pygame.Surface(px_size, pygame.SRCALPHA)

    assert stoptime.trip is not None
    line_number_render = font_bold.get_size(font_height).render(str(stoptime.trip.route.shortName), True, Colors.WHITE)
    line_headsign_render = font_regular.get_size(round(font_height * 0.9)).render(str(stoptime.headsign), True, Colors.WHITE)

    surf.blit(line_number_render, (0, px_size[1] // 2 - line_number_render.get_height() // 2))
    surf.blit(line_headsign_render, (px_size[0] // 5, px_size[1] // 2 + line_number_render.get_height() // 2 - line_headsign_render.get_height()))

    assert stoptime.realtimeDeparture is not None and stoptime.scheduledDeparture is not None
    departure: datetime.datetime = stoptime.realtimeDeparture if stoptime.realtime == True else stoptime.scheduledDeparture
    now = datetime.datetime.now()
    if departure < now:
        departure = now
    departure_time_text: str
    if stoptime.realtime == True and stoptime.realtimeState not in (RealtimeState.SCHEDULED, RealtimeState.CANCELED):
        departure_diff = departure - now
        departure_time_text = str(round(departure_diff.seconds / 60))
    else:
        departure_time_text = departure.strftime(core.renderers.time.TIMEFORMAT)

    departure_time_render = font_bold.get_size(font_height).render(departure_time_text, True, Colors.WHITE)
    # render strikethrough if canceled.
    if stoptime.realtimeState == RealtimeState.CANCELED:
        departure_time_size = departure_time_render.get_size()
        strikethrough_y = round(departure_time_size[1] / 2)
        strikethrough_w = max(round(departure_time_size[1] / 14), 1)
        pygame.draw.line(
            departure_time_render, Colors.WHITE,
            (0, strikethrough_y), (departure_time_size[0], strikethrough_y),
            strikethrough_w
        )

    surf.blit(departure_time_render, (px_size[0] - departure_time_render.get_width(), px_size[1] // 2 - departure_time_render.get_height() // 2))

    return surf
