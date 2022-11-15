from __future__ import annotations
from abc import ABC, abstractmethod
import datetime
import pygame

class Embed(ABC):
    def __init__(self, *args: str):
        pass

    @abstractmethod
    def on_enable(self):
        pass

    @abstractmethod
    def on_disable(self):
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface, content_spacing: int, approx_datetime: datetime.datetime, progress: float):
        pass

    @staticmethod
    @abstractmethod
    def name() -> str:
        raise NotImplementedError("Embed name must be implemented!")

    @abstractmethod
    def requested_duration(self) -> float:
        raise NotImplementedError("Embed duration must be implemented!")



from embeds.alert_embed import AlertEmbed
from embeds.weather_embed import WeatherEmbed
from embeds.line_embed import LineEmbed

ALL_EMBEDS: tuple[type[Embed], ...] = (
    WeatherEmbed,
    AlertEmbed,
    LineEmbed
)
