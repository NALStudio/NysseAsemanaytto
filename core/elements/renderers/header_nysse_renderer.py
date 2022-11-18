import pygame
from core import elements

class HeaderNysseRenderer(elements.ElementRenderer):
    def update(self, context: elements.UpdateContext) -> bool:
        return False

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        header_rect: pygame.Rect = params.header_rect

        w: int = header_rect.height * 6 # *6 should be enough to contain the logo
        h: int = round(header_rect.height * 0.7)

        x: int = header_rect.left + header_rect.width // 5
        y: int = header_rect.centery - (h // 2)

        return pygame.Rect(x, y, w, h)

    def render(self, size: tuple[int, int]) -> pygame.Surface | None:
        nysse_logo_unscaled = pygame.image.load("resources/textures/logos/nysse/logo.png").convert_alpha()

        target_height: int = size[1]
        target_width: int = round((nysse_logo_unscaled.get_width() / nysse_logo_unscaled.get_height()) * target_height)

        nysse_logo = pygame.transform.smoothscale(nysse_logo_unscaled, (target_width, target_height))

        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.blit(nysse_logo, (0, size[1] // 2 - nysse_logo.get_height() // 2))

        return surf
