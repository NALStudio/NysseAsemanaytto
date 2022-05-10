from digitransit.enums import RealtimeState
from core.colors import Colors
import pygame
import core.renderers.time
import pygame.font
import datetime
from digitransit.routing import Stoptime

font_small: pygame.font.Font | None = None
font: pygame.font.Font | None = None
font_height: int | None = None

def renderStoptime(px_size: tuple[int, int], stoptime: Stoptime) -> pygame.Surface:
    global font_small, font, font_height
    target_font_height: int = px_size[1] - round(px_size[1] / 3)
    if font_small is None or font is None or font_height != target_font_height:
        font_height = target_font_height
        font = pygame.font.Font("resources/fonts/Lato-Bold.ttf", font_height)
        font_small = pygame.font.Font("resources/fonts/Lato-Regular.ttf", round(font_height * 0.9))

    surf = pygame.Surface(px_size, pygame.SRCALPHA)

    line_number_render = font.render(str(stoptime.trip.routeShortName), True, Colors.WHITE)
    line_headsign_render = font_small.render(str(stoptime.headsign), True, Colors.WHITE)

    surf.blit(line_number_render, (0, px_size[1] // 2 - line_number_render.get_height() // 2))
    surf.blit(line_headsign_render, (px_size[0] // 5, px_size[1] // 2 + line_number_render.get_height() // 2 - line_headsign_render.get_height()))

    departure: datetime.datetime = stoptime.realtimeDeparture if stoptime.realtime else stoptime.scheduledDeparture
    now = datetime.datetime.now()
    if departure < now:
        departure = now
    stop_time_text: str
    if stoptime.realtime and stoptime.realtimeState != RealtimeState.SCHEDULED:
        departure_diff = departure - now
        stop_time_text = str(round(departure_diff.seconds / 60))
    else:
        stop_time_text = departure.strftime(core.renderers.time.TIMEFORMAT)

    departure_render = font.render(stop_time_text, True, Colors.WHITE)
    surf.blit(departure_render, (px_size[0] - departure_render.get_width(), px_size[1] // 2 - departure_render.get_height() // 2))

    return surf
