from __future__ import annotations
from abc import ABC, abstractmethod
import datetime
import time
from typing import Iterable

import pygame
from core import weather_handler
from core import colors


class Embed(ABC):
    def __init__(self, *args):
        pass

    @abstractmethod
    def on_enable(self):
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface):
        pass

    @staticmethod
    @abstractmethod
    def name() -> str:
        raise NotImplementedError("Embed name must be implemented!")

    @staticmethod
    @abstractmethod
    def duration() -> float:
        raise NotImplementedError("Embed duration must be implemented!")

class WeatherEmbed(Embed):
    def __init__(self, *args):
        self.fmi_place: str = args[0]
        assert isinstance(self.fmi_place, str), "First argument must be a Finnish Meteorological Institute place string!"

        self.refresh_rate: float = 3600.0

        self.last_update: float | None = None
        self.weather: list[weather_handler.Weather] | None = None
        self.time_font: pygame.font.Font | None = None
        self.time_font_height: int | None = None
        self.hour_count: int = 12

    def _set_weather(self, weather: Iterable[weather_handler.Weather]):
        self.weather = list(weather)

    def on_enable(self):
        now_update = time.process_time()
        if self.last_update is None or now_update - self.last_update > self.refresh_rate:
            print(f"Loading new weather data... ({self.fmi_place})")

            duration = datetime.timedelta(hours=self.hour_count) # 12 because I don't trust 11.
            params = weather_handler.WeatherFetchParams(duration, 3 * 60)
            weather_handler.get_weather(self.fmi_place, params, self._set_weather)
            self.utc_offset = datetime.datetime.now().utcoffset()
            self.last_update = now_update
            # Not adding difference but rather setting the value
            # because accuracy is not really important
            # and it works nicer with the None check.

    def render(self, surface: pygame.Surface):
        BACKGROUND_COLOR = colors.Colors.WHITE

        # raise NotImplementedError()
        surface.fill(BACKGROUND_COLOR)

        if self.weather is None:
            return
        assert len(self.weather) > 0, "No weather data provided!"

        COUNT = 3

        stat_width: float = surface.get_width() / COUNT
        common_surf: pygame.Surface = pygame.Surface((int(stat_width), surface.get_height()))
        for i in range(COUNT):
            common_surf.fill(BACKGROUND_COLOR)
            self.render_weather_stat(common_surf, self.weather[i])
            surface.blit(common_surf, (round(i * stat_width), 0))

    def render_weather_stat(self, surface: pygame.Surface, weather: weather_handler.Weather):
        target_time_font_height: int = round(surface.get_height() / 7)
        if self.time_font is None or self.time_font_height != target_time_font_height:
            print("Loading new time font...")
            self.time_font = pygame.font.Font("resources/fonts/Lato-Regular.ttf", target_time_font_height)
            self.time_font_height = target_time_font_height

        size = surface.get_size()
        center = (size[0] / 2, size[1] / 2)

        degree = self.time_font.render(f"{weather.temperature}°C", True, colors.Colors.BLACK)
        surface.blit(degree, (round(center[0] - degree.get_width() / 2), round(center[1])))

        symbol = weather_handler.get_weather_symbol(weather.symbol_id)
        symbol_size: int = round(surface.get_height() * 0.4)
        symbol = pygame.transform.smoothscale(symbol, (symbol_size, symbol_size))
        surface.blit(symbol, (round(center[0] - symbol_size / 2), round(center[1] - symbol_size)))

        time = self.time_font.render((weather.time_local).strftime("%H:%M"), True, colors.Colors.BLACK)
        surface.blit(time, (round(center[0] - time.get_width() / 2), round(center[1] + symbol_size - time.get_height())))

    @staticmethod
    def name() -> str:
        return "weather"

    @staticmethod
    def duration() -> float:
        return 15.0
