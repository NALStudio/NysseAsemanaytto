import pygame
import pygame.surface
import nysse.background_generator
from core import logging

background: pygame.Surface | None = None

def render_background(px_size: tuple[int, int]) -> pygame.Surface:
    global background

    if background is None or background.get_size() != px_size:
        logging.debug("Generating new wave for background rendering...", stack_info=False)
        background = nysse.background_generator.generateBackground(px_size).convert()

    return background
