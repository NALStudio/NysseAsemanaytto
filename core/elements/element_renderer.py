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
        """Called repeatedly to refresh this element's data. Return `True` to render this element with the updated data."""
        raise NotImplementedError()

    @abstractmethod
    def get_rect(self) -> pygame.Rect:
        """Compute the global rect of this element."""
        raise NotImplementedError()

    @abstractmethod
    def render(self, size: tuple[int, int], flags: elements.RenderFlags) -> pygame.Surface | None:
        """
        Render this element onto a surface with the specified size. Return `None` to clear this area of the screen.
        Return `None` to clear this area of the screen and adjust the flags-object to modify rendering behaviour.

        Should not modify the state of this element.
        """
        raise NotImplementedError()
