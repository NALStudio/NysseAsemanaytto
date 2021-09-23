import pygame
import nysse.background_generator
from typing import Optional, Tuple

background: Optional[pygame.Surface] = None

def renderBackground(px_size: Tuple[int, int]) -> pygame.Surface:
    global background

    if background == None or background.get_size() != px_size:
        print("Generating new wave for background rendering...")
        background = nysse.background_generator.generateBackground(px_size)

    return background