from abc import ABC, abstractmethod

import pygame
from core import elements

class ElementRenderer(ABC):
    @abstractmethod
    def setup(self) -> None:
        """Called after initializing the renderer. Can be used to load textures."""
        pass

    @abstractmethod
    def update(self, context: elements.UpdateContext) -> bool:
        """Called repeatedly to refresh this element's data."""
        raise NotImplementedError()

    @abstractmethod
    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        """Compute the global rect of this element."""
        raise NotImplementedError()

    @abstractmethod
    def render(self, size: tuple[int, int]) -> pygame.Surface | None:
        """Render this element onto a surface with the specified size."""
        raise NotImplementedError()
