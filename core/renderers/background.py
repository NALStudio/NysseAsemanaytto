import pygame
import pygame.surface
import nysse.background_generator
from core import logging

background: pygame.surface.Surface | None = None

def renderBackground(px_size: tuple[int, int]) -> pygame.surface.Surface:
    global background

    if background is None or background.get_size() != px_size:
        logging.debug("Generating new wave for background rendering...", stack_info=False)
        background = nysse.background_generator.generateBackground(px_size).convert()

    return background
