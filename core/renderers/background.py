import pygame
import pygame.surface
import nysse.background_generator

background: pygame.surface.Surface | None = None

def renderBackground(px_size: tuple[int, int]) -> pygame.surface.Surface:
    global background

    if background is None or background.get_size() != px_size:
        print("Generating new wave for background rendering...")
        background = nysse.background_generator.generateBackground(px_size).convert()

    return background
