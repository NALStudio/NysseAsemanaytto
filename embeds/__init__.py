from __future__ import annotations
from abc import ABC, abstractmethod
from types import EllipsisType
from typing import NamedTuple
import pygame
from core import elements

class EmbedContext(NamedTuple):
    first_frame: bool
    update: elements.UpdateContext

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
    def update(self, context: EmbedContext, progress: float) -> bool | EllipsisType:
        """
        Called repeatedly to refresh this embed's data.
        Return `True` to render this embed with the updated data.
        Return `...` to render using the previous frame of this embed if possible.
        """
        raise NotImplementedError()

    @abstractmethod
    def render(self, size: tuple[int, int], flags: elements.RenderFlags) -> pygame.Surface | None:
        """
        Render this embed onto a surface with the specified size.
        Return `None` to clear this area of the screen and adjust the flags-object to modify rendering behaviour.

        Should not modify the state of this embed.
        """
        raise NotImplementedError()

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
