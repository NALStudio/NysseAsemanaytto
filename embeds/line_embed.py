from __future__ import annotations
import datetime
import threading
from typing import NamedTuple, Sequence

import embeds
import digitransit.routing
import pygame
import pygame.gfxdraw
import pyproj
import nysse.styles
import nysse.vehicle_monitoring

from core import render_info, logging, config, font_helper, colors
from nalpy import math
import digitransit.routing

data_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lota-Grotesque-Regular.otf", "line data rendering")
data_font_bold: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lota-Grotesque-Bold.otf", "line data number rendering")

vehicle_line_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/OpenSans-Regular.ttf", "vehicle line number rendering")

class CachedLineRender(NamedTuple):
    surface: pygame.Surface
    reference_limits: math.Rect
    size: tuple[int, int]
    top_padding_extra: int
    padding: int
    line_thickness: int

class LineEmbed(embeds.Embed):
    def __init__(self, *args: str):
        self.trip: digitransit.routing.Trip | None = None
        self.active_lines: set[digitransit.routing.Pattern]

        self.display_vehicles: bool = False
        if len(args) > 0:
            self.display_vehicles = bool(args[0])

        self.vehicle_positions: tuple[nysse.vehicle_monitoring.MonitoredVehicleJourney, ...] | None = None
        self.rendered_vehicle_positions: pygame.Surface | None = None
        self.vehicle_request_thread: threading.Thread | None = None

    def on_enable(self):
        assert render_info.stopinfo.stoptimes is not None
        self.trip = render_info.stopinfo.stoptimes[0].trip
        assert self.trip is not None

        route_shortname: str | None = self.trip.route.shortName
        assert route_shortname is not None

        if self.vehicle_request_thread is not None and self.vehicle_request_thread.is_alive():
            logging.warning("Vehicle request thread still active. Waiting for thread to finish...")
            self.vehicle_request_thread.join()

        self.vehicle_positions = None
        self.rendered_vehicle_positions = None
        self.vehicle_request_thread = threading.Thread(target=self._get_positions, args=(route_shortname,), name=f"VehicleRequest_{route_shortname}")
        self.vehicle_request_thread.start()

    def _get_positions(self, route_shortname: str):
        client_id: str | None = config.current.nysse_api_client_id
        client_secret: str | None = config.current.nysse_api_client_secret
        if client_id is None or client_secret is None:
            raise ValueError("Nysse API client ID and client secret must be defined for vehicle positions in line embed.")

        self.vehicle_positions = nysse.vehicle_monitoring.get_monitored_vehicle_journeys(client_id, client_secret, route_shortname)

    def on_disable(self):
        self.trip = None

    def render(self, surface: pygame.Surface, content_spacing: int, approx_datetime: datetime.datetime, progress: float):
        global last_render_cache_clear, line_render_cache_size

        trip = self.trip
        assert trip is not None

        surface_size: tuple[int, int] = surface.get_size()

        if last_render_cache_clear is None or (approx_datetime - last_render_cache_clear).days > 1:
            last_render_cache_clear = approx_datetime
            line_render_cache.clear()

        if line_render_cache_size is None or line_render_cache_size != surface_size:
            line_render_cache_size = surface_size
            line_render_cache.clear()

        patternCode = trip.patternCode
        if patternCode not in line_render_cache:
            rendered: CachedLineRender | None = render_embed_for_pattern(patternCode, surface_size)
            if rendered is None:
                logging.error("Map line could not be rendered.")
                return
            else:
                line_render_cache[patternCode] = rendered

        cached_render: CachedLineRender = line_render_cache[patternCode]
        surface.blit(cached_render.surface, (0, 0))

        if self.rendered_vehicle_positions is None:
            if self.vehicle_positions is not None:
                self.rendered_vehicle_positions = render_vehicle_positions(cached_render, self.vehicle_positions)
        else:
            surface.blit(self.rendered_vehicle_positions, (0, 0))

    @staticmethod
    def name() -> str:
        return "lines"

    def requested_duration(self) -> float:
        return 15.0

last_render_cache_clear: datetime.datetime | None = None
line_render_cache_size: tuple[int, int] | None = None
line_render_cache: dict[str, CachedLineRender] = {}

class _RemappedPoints(NamedTuple):
    points: list[math.Vector2]
    restrictingDimension: tuple[bool, bool]

def _point_limits(points: Sequence[math.Vector2]) -> math.Rect:
    ref_x_vals: list[float] = [p.x for p in points]
    ref_y_vals: list[float] = [p.y for p in points]

    left = min(ref_x_vals)
    right = max(ref_x_vals)
    top = max(ref_y_vals) # up is positive for y
    bottom = min(ref_y_vals)

    return math.Rect.from_sides(left, top, right, bottom)

def _remapPoints(unscaled_points: Sequence[math.Vector2], limits: math.Rect, size: tuple[float, float], top_padding_extra: int, padding: int) -> _RemappedPoints:
    target_left: float = padding
    target_right: float = size[0] - padding
    target_top: float = padding + top_padding_extra # down is positive for y
    target_bottom: float = size[1] - padding

    width: float = abs(limits.right - limits.left)
    height: float = abs(limits.bottom - limits.top)
    width_scale_aspect: float = abs(target_right - target_left) / width
    height_scale_aspect: float = abs(target_bottom - target_top) / height

    restrictingDimension: tuple[bool, bool]
    if width_scale_aspect > height_scale_aspect: # map is not wide enough => height is the restricting component
        scale_to_width: float = width * height_scale_aspect
        target_left = (size[0] - scale_to_width) / 2
        target_right = size[0] - target_left

        restrictingDimension = (False, True)
    else: # map is not high enough => width is the restricting component
        scale_to_height: float = height * width_scale_aspect
        target_top = (size[1] - scale_to_height) / 2  # down is positive for y
        target_bottom = size[1] - target_top

        restrictingDimension = (True, False)

    def remapper(point: math.Vector2):
        x = math.remap(point.x, limits.left, limits.right, target_left, target_right)
        y = math.remap(point.y, limits.top, limits.bottom, target_top, target_bottom)
        return math.Vector2(x, y)

    remapped_points: list[math.Vector2] = [remapper(p) for p in unscaled_points]
    return _RemappedPoints(remapped_points, restrictingDimension)

class Tetragon(NamedTuple):
    topleft: math.Vector2
    topright: math.Vector2
    bottomright: math.Vector2
    bottomleft: math.Vector2
    segment: math.Vector2

    def to_int_tuple(self) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
        return (
            self.topleft.to_int_tuple(),
            self.topright.to_int_tuple(),
            self.bottomright.to_int_tuple(),
            self.bottomleft.to_int_tuple()
        )

def _line_to_tetragon(p1: math.Vector2, p2: math.Vector2, thickness: int) -> Tetragon:
    half_thickness: float = thickness / 2
    segment = p2 - p1

    perp = math.Vector2.perpendicular(segment)
    bottom_offset = perp.normalized * half_thickness # bottom because y goes down.
    top_offset = -bottom_offset

    tet: Tetragon = Tetragon(
        topleft=p1 + top_offset,
        topright=p2 + top_offset,
        bottomright=p2 + bottom_offset,
        bottomleft=p1 + bottom_offset,
        segment=segment
    )

    return tet

def _draw_joined_aalines(surface: pygame.Surface, color: tuple[int, int, int], points: Sequence[math.Vector2], thickness: int):
    if len(points) < 3:
        raise ValueError("A minimum of 3 points must be provided.")

    def _draw_line(line_tetragon: Tetragon):
        rounded = line_tetragon.to_int_tuple()
        pygame.gfxdraw.aapolygon(surface, rounded, color)
        pygame.gfxdraw.filled_polygon(surface, rounded, color)

    # draw lines
    for i in range(1, len(points) - 1):
        last_i: int = i - 1
        current_i: int = i
        next_i: int = i + 1

        last_p = points[last_i]
        current_p = points[current_i]
        next_p = points[next_i]

        # Line segments as tetragons
        first_s: Tetragon = _line_to_tetragon(last_p, current_p, thickness)
        second_s: Tetragon = _line_to_tetragon(current_p, next_p, thickness)

        # Draw line(s)
        _draw_line(first_s)
        if next_i >= len(points) - 1: # If next point is final point, draw a line to it.
            _draw_line(second_s)

        # Draw line joint
        segment_angle: float = math.Vector2.signed_angle(first_s.segment, second_s.segment)
        segment_close_to_straight: bool = math.isclose(abs(segment_angle), 180) or math.isclose(segment_angle, 0)
        if not segment_close_to_straight: # determine on which side the joint should be drawn
            joint: list[tuple[int, int]] = [current_p.to_int_tuple()]
            if segment_angle < 0:
                joint.append(first_s.bottomright.to_int_tuple())
                joint.append(second_s.bottomleft.to_int_tuple())
            else: # segment_angle > 0 when segment_angle != 0
                joint.append(first_s.topright.to_int_tuple())
                joint.append(second_s.topleft.to_int_tuple())

            pygame.gfxdraw.aapolygon(surface, joint, color)
            pygame.gfxdraw.filled_polygon(surface, joint, color)

    # draw line ends
    def _draw_line_end(point: math.Vector2):
        r: int = round(thickness / 2)
        x, y = point.to_int_tuple()
        pygame.gfxdraw.aacircle(surface, x, y, r, color)
        pygame.gfxdraw.filled_circle(surface, x, y, r, color)
    _draw_line_end(points[0])
    _draw_line_end(points[-1])

    return surface

def _closest_point_in_polygon(point: math.Vector2, shape: Sequence[math.Vector2]) -> math.Vector2:
    minDist: float | None = None
    minPoint: math.Vector2 | None = None

    # Modified from: https://stackoverflow.com/questions/10983872/distance-from-a-point-to-a-polygon
    for i in range(len(shape) - 1):
        p1 = shape[i]
        p2 = shape[i + 1]

        segment = p2 - p1
        to_point = point - p1

        r = math.Vector2.dot(segment, to_point)
        r /= math.pow(segment.magnitude, 2)

        dist: float
        ref_point: math.Vector2
        if r < 0:
            dist = to_point.magnitude
            ref_point = p1
        elif r > 1:
            dist = (p2 - point).magnitude
            ref_point = p2
        else: # To understand the maths of Case 3: https://i.stack.imgur.com/B9vX0.png
            portion_of_segment: math.Vector2 = segment * r
            closest_point_on_segment: math.Vector2 = p1 + portion_of_segment
            dist = (point - closest_point_on_segment).magnitude
            # dist = math.sqrt(math.pow(to_point.magnitude, 2.0) - math.pow((portion_of_segment.magnitude), 2.0))
            ref_point = closest_point_on_segment

        if minDist is None or minDist > dist:
            minDist = dist
            minPoint = ref_point

    assert minDist is not None
    assert minPoint is not None
    return minPoint

def _draw_stop(surface: pygame.Surface, point: math.Vector2, line_geometry: Sequence[math.Vector2], line_thickness: float):
    closest_point_on_line: math.Vector2 = _closest_point_in_polygon(point, line_geometry)

    x, y = closest_point_on_line.to_int_tuple()
    r: int = round(line_thickness * 0.6)
    pygame.gfxdraw.aacircle(surface, x, y, r, colors.Colors.WHITE)
    pygame.gfxdraw.filled_circle(surface, x, y, r, colors.Colors.WHITE)
    pygame.gfxdraw.aacircle(surface, x, y, r, colors.Colors.BLACK)

def _renderData(pattern: digitransit.routing.Pattern, height: int, padding: int) -> pygame.Surface | None:
    pictogram_size: int = height - 2 * padding
    data_font_size: int = round(0.8 * pictogram_size)
    small_data_font_size: int = round(0.6 * pictogram_size)
    sized_font_bold = data_font_bold.get_size(data_font_size)
    sized_font = data_font.get_size(small_data_font_size)

    if pattern.route.mode is None:
        return None
    pictogram = nysse.styles.load_pictogram_by_mode(pattern.route.mode, True)
    if pictogram is None:
        return None
    pictogram = pygame.transform.smoothscale(pictogram, (pictogram_size, pictogram_size)).convert_alpha()

    data_number: pygame.Surface = sized_font_bold.render(f"{pattern.route.shortName} ", True, colors.Colors.WHITE)
    data: pygame.Surface = sized_font.render(pattern.route.longName, True, colors.Colors.WHITE)

    centery = height / 2
    pictogram_rect: pygame.Rect = pygame.Rect(padding, round(centery - pictogram.get_height() / 2), *pictogram.get_size())
    data_number_rect: pygame.Rect = pygame.Rect(pictogram_rect.right + padding, round(centery - data_number.get_height() / 2), *data_number.get_size())
    data_rect: pygame.Rect = pygame.Rect(data_number_rect.right, round(centery - data.get_height() / 2), *data.get_size())

    surf = pygame.Surface((data_rect.right + padding, height), pygame.SRCALPHA)

    pygame.draw.rect(surf, colors.NysseColors.TUMMANSININEN, (0, 0, *surf.get_size()), border_radius=round(height / 4))

    surf.blit(pictogram, pictogram_rect.topleft)
    surf.blit(data_number, data_number_rect.topleft)
    surf.blit(data, data_rect.topleft)

    return surf

def render_embed_for_pattern(patternCode: str, size: tuple[int, int]) -> CachedLineRender | None:
    pattern: digitransit.routing.Pattern | None = _get_pattern(patternCode)
    if pattern is None:
        return None

    padding: int = round(size[1] / 25)

    data_surf = _renderData(pattern, round(size[1] / 8), round(padding * 0.75))
    if data_surf is None:
        logging.error("Could not render data surface for line embed.")
        data_surf = pygame.Surface((padding, padding))
        data_surf.fill((255, 0, 0))
    data_rect: pygame.Rect = pygame.Rect(padding, padding, *data_surf.get_size())

    line: CachedLineRender = _render_line_for_pattern(pattern, size, padding, data_rect)
    line.surface.blit(data_surf, data_rect.topleft)

    return line

def _get_pattern(patternCode: str) -> digitransit.routing.Pattern | None:
    pattern: digitransit.routing.Pattern | None = None
    try:
        pattern = digitransit.routing.get_pattern(config.current.endpoint, patternCode)
    except Exception as e:
        logging.dump_exception(e, note="lineEmbed")

    return pattern

vehicle_base: pygame.Surface | None = None
def _draw_vehicle(surface: pygame.Surface, center: math.Vector2, bearing: float, line_thickness: int) -> None:
    global vehicle_base
    if vehicle_base is None:
        vehicle_base = pygame.image.load("resources/textures/elements/line_map/vehicle.png").convert_alpha()

    target_size: int = 6 * line_thickness
    scale_factor: float = target_size / vehicle_base.get_height()

    vehicle_dir: float = -bearing + 90 # direction reference from north to east and from counter-clockwise to clockwise
    scaled_vehicle = pygame.transform.rotozoom(vehicle_base, vehicle_dir, scale_factor)

    x: float = center.x - (scaled_vehicle.get_width() / 2)
    y: float = center.y - (scaled_vehicle.get_height() / 2)

    surface.blit(scaled_vehicle, (round(x), round(y)))

def render_vehicle_positions(base_map: CachedLineRender, vehicles: Sequence[nysse.vehicle_monitoring.MonitoredVehicleJourney]) -> pygame.Surface:
    unscaled_vehicle_points: list[math.Vector2] = [_projectCoordinates(vehicle.vehicle_location) for vehicle in vehicles]
    vehicles_remapped = _remapPoints(unscaled_vehicle_points, base_map.reference_limits, base_map.size, base_map.top_padding_extra, base_map.padding)

    surf: pygame.Surface = pygame.Surface(base_map.size, pygame.SRCALPHA)

    for point, vehicle in zip(vehicles_remapped.points, vehicles):
        _draw_vehicle(surf, point, vehicle.bearing, base_map.line_thickness)

    return surf

def _render_line_for_pattern(pattern: digitransit.routing.Pattern, size: tuple[int, int], padding: int, line_data_rect: pygame.Rect) -> CachedLineRender:
    assert pattern.route.mode is not None
    line_color: tuple[int, int, int] = nysse.styles.get_color_by_mode(pattern.route.mode)

    unscaled_line_points: list[math.Vector2] = [_projectCoordinates(coordinate) for coordinate in pattern.geometry]
    ref_limits: math.Rect = _point_limits(unscaled_line_points)

    top_padding_extra: int = 0
    line_remapped: _RemappedPoints = _remapPoints(unscaled_line_points, ref_limits, size, top_padding_extra, padding)
    # If line collides with data box, make the line area smaller
    if any(line_data_rect.collidepoint(*p.to_int_tuple()) for p in line_remapped.points):
        top_padding_extra = line_data_rect.bottom
        line_remapped = _remapPoints(unscaled_line_points, ref_limits, size, top_padding_extra, padding)

    line_thickness = round(max(min(size) / 75, 1))

    surface: pygame.Surface = pygame.Surface(size)
    surface.fill((255, 255, 255))
    _draw_joined_aalines(surface, line_color, line_remapped.points, line_thickness)

    unscaled_stop_points: list[math.Vector2] = [_projectCoordinates(stop.coordinate) for stop in pattern.stops]
    stop_remapped = _remapPoints(unscaled_stop_points, ref_limits, size, top_padding_extra, padding)
    for stop_point in stop_remapped.points:
        _draw_stop(surface, stop_point, line_remapped.points, line_thickness)

    return CachedLineRender(surface, ref_limits, size, top_padding_extra, padding, line_thickness)


lonlat_to_webmercator: pyproj.Transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def _projectCoordinates(coordinate: digitransit.routing.Coordinate | nysse.vehicle_monitoring.Coordinate) -> math.Vector2:
    x, y = lonlat_to_webmercator.transform(coordinate.longitude, coordinate.latitude)
    return math.Vector2(x, y)
