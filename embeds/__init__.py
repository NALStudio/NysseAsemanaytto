from __future__ import annotations
from abc import ABC, abstractmethod
import datetime
import time
import digitransit.routing
from typing import Iterable

import pygame
from core import weather_handler
from core import colors
from core import config

class Embed(ABC):
    def __init__(self, *args: str):
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



from embeds.alert_embed import AlertEmbed
from embeds.weather_embed import WeatherEmbed

ALL_EMBEDS: tuple[type[Embed], ...] = (
    WeatherEmbed,
    AlertEmbed
)
