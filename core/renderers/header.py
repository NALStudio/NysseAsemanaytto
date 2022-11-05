import pygame
import pygame.image
import pygame.surface
import pygame.transform
import nysse.pictogram
import core.renderers.time as time_renderer
from digitransit.enums import Mode
from core import logging

transport_icon: pygame.Surface | None = None
nysse_logo: pygame.Surface | None = None

def render_header(px_size: tuple[int, int], vehicleMode: Mode) -> pygame.Surface:
    global transport_icon, nysse_logo
    if transport_icon is None or transport_icon.get_height() != px_size[1]:
        logging.debug("Loading new transport icon for header...", stack_info=False)
        transport_icon = nysse.pictogram.load_pictogram_by_mode(vehicleMode)
        if transport_icon is not None:
            transport_icon = pygame.transform.smoothscale(transport_icon, (px_size[1], px_size[1])).convert_alpha()
        else:
            logging.error(f"Could not load pictogram for mode: {vehicleMode.name}")

    nysse_logo_height: float = px_size[1] * 0.7
    if nysse_logo is None or nysse_logo.get_height() != round(nysse_logo_height):
        logging.debug("Loading new Nysse logo for header...", stack_info=False)
        nysse_logo = pygame.image.load("resources/textures/logos/nysse/logo.png")
        nysse_logo_width: float = nysse_logo.get_width() / nysse_logo.get_height() * nysse_logo_height
        nysse_logo = pygame.transform.smoothscale(nysse_logo, (round(nysse_logo_width), round(nysse_logo_height))).convert_alpha()

    surf = pygame.Surface(px_size, pygame.SRCALPHA)
    if transport_icon is not None:
        surf.blit(transport_icon, (0, 0))

    surf.blit(nysse_logo, (px_size[0] // 5, px_size[1] // 2 - nysse_logo.get_height() // 2))

    time_render = time_renderer.render_time(px_size[1])
    surf.blit(time_render, (px_size[0] - time_render.get_width(), px_size[1] - time_render.get_height())) # Height aligned from bottom because font has whitespace above each letter

    return surf
