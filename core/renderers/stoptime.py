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

def renderStoptime(px_size: tuple[int, int], stoptime: Stoptime) -> pygame.Surface:
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
    stop_time_text: str
    if stoptime.realtime and stoptime.realtimeState != RealtimeState.SCHEDULED:
        departure_diff = departure - now
        stop_time_text = str(round(departure_diff.seconds / 60))
    else:
        stop_time_text = departure.strftime(core.renderers.time.TIMEFORMAT)

    departure_render = font_bold.get_size(font_height).render(stop_time_text, True, Colors.WHITE)
    surf.blit(departure_render, (px_size[0] - departure_render.get_width(), px_size[1] // 2 - departure_render.get_height() // 2))

    return surf
