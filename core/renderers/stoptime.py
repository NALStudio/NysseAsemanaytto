from digitransit.enums import RealtimeState
from core.colors import Colors
from core import font_helper, testing, logging
import pygame
import core.renderers.time
import pygame.font
import datetime
from digitransit.routing import Stoptime

font_bold: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Bold.ttf")
font_regular: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Regular.ttf")

line_data_render_cache_size: tuple[int, int] | None = None
line_data_render_cache: dict[tuple[str, str], pygame.Surface] = {}

def _render_line_data(px_size: tuple[int, int], font_height: int, shortname: str, headsign: str):
    surf = pygame.Surface(px_size, pygame.SRCALPHA)

    line_number_render = font_bold.get_size(font_height).render(shortname, True, Colors.WHITE)
    line_headsign_render = font_regular.get_size(round(font_height * 0.9)).render(headsign, True, Colors.WHITE)

    surf.blit(line_number_render, (0, px_size[1] // 2 - line_number_render.get_height() // 2))
    surf.blit(line_headsign_render, (px_size[0] // 5, px_size[1] // 2 + line_number_render.get_height() // 2 - line_headsign_render.get_height()))

    return surf

def render_stoptime(px_size: tuple[int, int], stoptime: Stoptime, current_time: datetime.datetime) -> pygame.Surface:
    global line_data_render_cache_size
    font_height: int = px_size[1] - round(px_size[1] / 3)

    #region Departure Data
    assert stoptime.trip is not None
    shortname = stoptime.trip.route.shortName
    headsign = stoptime.headsign
    assert shortname is not None
    assert headsign is not None
    line_cache_key: tuple[str, str] = (shortname, headsign)

    if line_data_render_cache_size != px_size:
        logging.debug("Clearing line data render cache...", stack_info=False)
        line_data_render_cache.clear()
        line_data_render_cache_size = px_size

    if line_cache_key not in line_data_render_cache:
        logging.debug(f"Rendering data for line: {line_cache_key}...", stack_info=False)
        line_data_render_cache[line_cache_key] = _render_line_data(px_size, font_height, shortname, headsign)
    data_surf: pygame.Surface = line_data_render_cache[line_cache_key].copy()
    #endregion

    #region Departure Time
    assert stoptime.realtimeDeparture is not None and stoptime.scheduledDeparture is not None
    departure: datetime.datetime = stoptime.realtimeDeparture if stoptime.realtime == True else stoptime.scheduledDeparture
    if departure < current_time:
        departure = current_time
    departure_time_text: str
    if stoptime.realtime == True and stoptime.realtimeState not in (RealtimeState.SCHEDULED, RealtimeState.CANCELED):
        departure_diff = departure - current_time
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
    #endregion

    data_surf.blit(departure_time_render, (px_size[0] - departure_time_render.get_width(), px_size[1] // 2 - departure_time_render.get_height() // 2))

    return data_surf
