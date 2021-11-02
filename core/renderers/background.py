import pygame
import pygame.surface
import nysse.background_generator
from typing import Optional, Tuple

background: Optional[pygame.surface.Surface] = None

def renderBackground(px_size: Tuple[int, int]) -> pygame.surface.Surface:
    global background

    if background == None or background.get_size() != px_size:
        print("Generating new wave for background rendering...")
        background = nysse.background_generator.generateBackground(px_size).convert()

    return background