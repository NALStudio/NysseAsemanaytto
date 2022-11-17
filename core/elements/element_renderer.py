from abc import ABC, abstractmethod

import pygame
from core import elements

class ElementRenderer(ABC):
    @abstractmethod
    def update(self, context: elements.UpdateContext) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        raise NotImplementedError()

    @abstractmethod
    def render(self) -> pygame.Surface | None:
        raise NotImplementedError()
