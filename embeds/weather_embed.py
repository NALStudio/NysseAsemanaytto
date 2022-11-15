from __future__ import annotations

import embeds
from nalpy import math
from core import weather_handler, colors, font_helper, logging
import pygame
import time
from typing import Iterable, Sequence
import datetime

BACKGROUND_COLOR = colors.Colors.WHITE

class WeatherEmbed(embeds.Embed):
    def __init__(self, *args: str):
        assert len(args) == 1, "Invalid argument count!"

        self.fmi_place: str = args[0]
        assert isinstance(self.fmi_place, str), "First argument must be a Finnish Meteorological Institute place string!"

        self.refresh_rate: float = 3600.0 # seconds

        self.last_update: float | None = None
        self.weather: list[weather_handler.Weather] | None = None
        self.cached_weather_surface: pygame.Surface | None = None
        self.big_time_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Regular.ttf", "weather embed time rendering")
        self.small_time_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Regular.ttf", "weather embed time rendering")
        self.hour_count: int = 11 # (datapoint_count * 3) - 1

    def _set_weather(self, weather: Iterable[weather_handler.Weather]):
        self.weather = list(weather)
        self.cached_weather_surface = None # Force re-rendering of the weather data.

    def on_enable(self):
        def round_to_nearest_third_hour(dt: datetime.datetime):
            total_hours: float = dt.hour + dt.minute / 60.0
            rounded_hours: int = math.round_to_nearest_n(total_hours, 3)
            add_days, set_hours = divmod(rounded_hours, 24)
            dt += datetime.timedelta(days=add_days)
            return dt.replace(minute=0, second=0, microsecond=0, hour=set_hours)

        now_update = time.time()
        if self.last_update is None or (now_update - self.last_update) > self.refresh_rate:
            logging.info(f"Loading new weather data... ({self.fmi_place})", stack_info=False)

            starttime = round_to_nearest_third_hour(datetime.datetime.utcnow())
            duration = datetime.timedelta(hours=self.hour_count)
            params = weather_handler.WeatherFetchParams(starttime, duration, 3 * 60)
            weather_handler.get_weather(self.fmi_place, params, self._set_weather)
            self.last_update = now_update
            # Not adding difference but rather setting the value
            # because accuracy is not really important
            # and it works nicer with the None check.

    def on_disable(self):
        pass

    # This is re-rendered by the render() or _set_weather() methods.
    def render_cached_surface(self, size: tuple[int, int]) -> None:
        logging.debug("Rendering new weather embed...", stack_info=False)

        weather = self.weather
        if weather is None:
            logging.debug("Weather data is not loaded yet! Cancelling weather embed rendering...", stack_info=False)
            return

        HORIZONTAL_MARGIN = round(size[0] / 30)
        VERTICAL_MARGIN = HORIZONTAL_MARGIN
        surface = pygame.Surface(size)

        surface.fill(BACKGROUND_COLOR)

        COUNT = 4
        assert len(weather) == COUNT

        OTHER_EXTRA_VERTICAL_MARGIN: int = VERTICAL_MARGIN * 2
        CURRENT_OTHER_PADDING: int = HORIZONTAL_MARGIN * 2

        current_other_padding_half = CURRENT_OTHER_PADDING / 2
        total_width = surface.get_width() - (2 * HORIZONTAL_MARGIN)
        total_height = surface.get_height() - (2 * VERTICAL_MARGIN)

        other_width = ((total_width * math.GOLDEN_RATIO) / (math.GOLDEN_RATIO + 1)) - current_other_padding_half
        other_height = total_height - round(2.45 * OTHER_EXTRA_VERTICAL_MARGIN)
        if other_width < 0 or other_height < 0:
            return
        other_surf = pygame.Surface((other_width, other_height))

        current_width = total_width - other_width - current_other_padding_half
        if current_width < 0:
            return
        current_surf = pygame.Surface((round(current_width), total_height))

        self.render_current_weather(current_surf, weather[0])
        self.render_other_weathers(other_surf, weather[1:])

        surface.blit(current_surf, (HORIZONTAL_MARGIN, VERTICAL_MARGIN))
        surface.blit(other_surf, (current_width + CURRENT_OTHER_PADDING, VERTICAL_MARGIN + OTHER_EXTRA_VERTICAL_MARGIN))

        self.cached_weather_surface = surface

    def render(self, surface: pygame.Surface, content_spacing: int, approx_datetime: datetime.datetime, progress: float):
        target_size: tuple[int, int] = surface.get_size()

        if self.cached_weather_surface is None or self.cached_weather_surface.get_size() != target_size:
            self.render_cached_surface(target_size)

        if self.cached_weather_surface is not None:
            surface.blit(self.cached_weather_surface, (0, 0))

    def render_weather_stat(self, surface: pygame.Surface, weather: weather_handler.Weather):
        surface_size: tuple[int, int] = surface.get_size()
        surface.fill(BACKGROUND_COLOR)

        font = self.big_time_font.get_size(round(surface_size[1] / 8))

        symbol = weather_handler.get_weather_symbol(weather.symbol_id)
        symbol_width: int = symbol.get_width()
        symbol_size_multiplier = (surface_size[0] / symbol_width)
        symbol = pygame.transform.smoothscale(symbol, (round(symbol_width * symbol_size_multiplier), round(symbol.get_height() * symbol_size_multiplier)))
        surface.blit(symbol, (round((surface.get_width() / 2) - (symbol.get_width() / 2)), 0))

        time = font.render((weather.time_local).strftime("%H:%M"), True, colors.Colors.BLACK)
        temperature = font.render(f"{math.round_away_from_zero(weather.temperature)}°C", True, colors.Colors.BLACK)
        top = symbol.get_height()
        temperature_y = surface_size[1] - temperature.get_height()
        centerx = surface_size[0] / 2

        surface.blit(time, (round(centerx - time.get_width() / 2), round(math.lerp(top, temperature_y, 0.5) - time.get_height())))
        surface.blit(temperature, (round(centerx - temperature.get_width() / 2), temperature_y))

    def render_other_weathers(self, surface: pygame.Surface, weathers: Sequence[weather_handler.Weather]):
        surface.fill(BACKGROUND_COLOR)
        PADDING: float = surface.get_width() / 15

        stat_width: float = (surface.get_width() / len(weathers)) - (PADDING / 2)
        common_surf: pygame.Surface = pygame.Surface((round(stat_width), surface.get_height()))
        for i, weather in enumerate(weathers):
            common_surf.fill(BACKGROUND_COLOR)
            self.render_weather_stat(common_surf, weather)
            surface.blit(common_surf, (round(i * (stat_width + PADDING)), 0))

    def render_current_weather(self, surface: pygame.Surface, weather: weather_handler.Weather):
        surface_size: tuple[int, int] = surface.get_size()
        surface.fill(BACKGROUND_COLOR)

        font = self.big_time_font.get_size(round(surface_size[1] / 8))

        symbol = weather_handler.get_weather_symbol(weather.symbol_id)
        symbol_width: int = symbol.get_width()
        symbol_size_multiplier = (surface_size[0] / symbol_width)
        symbol = pygame.transform.smoothscale(symbol, (round(symbol_width * symbol_size_multiplier), round(symbol.get_height() * symbol_size_multiplier)))
        surface.blit(symbol, (round((surface.get_width() / 2) - (symbol.get_width() / 2)), 0))

        time = font.render((weather.time_local).strftime("%H:%M"), True, colors.Colors.BLACK)
        temperature = font.render(f"{math.round_away_from_zero(weather.temperature)}°C", True, colors.Colors.BLACK)
        y = round(surface_size[1] - 1.5 * max(time.get_height(), temperature.get_height()))

        surface.blit(time, (0, y))
        surface.blit(temperature, (surface_size[0] - temperature.get_width(), y))

    @staticmethod
    def name() -> str:
        return "weather"

    def requested_duration(self) -> float:
        return 15.0
