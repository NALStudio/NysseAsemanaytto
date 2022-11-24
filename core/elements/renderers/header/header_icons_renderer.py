import pygame
from core import elements
import nysse.styles
import digitransit.enums

class HeaderIconsRenderer(elements.ElementRenderer):
    def __init__(self) -> None:
        self.vehicle_mode: digitransit.enums.Mode | None = None

    def setup(self) -> None:
        pass

    def update(self, context: elements.UpdateContext) -> bool:
        changes: bool = False

        new_vehicleMode = context.stopinfo.vehicleMode
        if new_vehicleMode is not None and self.vehicle_mode != new_vehicleMode:
            self.vehicle_mode = new_vehicleMode
            changes = True

        return changes

    def get_rect(self) -> pygame.Rect:
        header_rect: pygame.Rect = elements.position_params.header_rect
        return pygame.Rect(header_rect.left, header_rect.top, header_rect.height, header_rect.height) # width is height, square

    def render(self, size: tuple[int, int], flags: elements.RenderFlags) -> pygame.Surface | None:
        assert self.vehicle_mode is not None, "Update should have assigned vehicle_mode already."
        transport_icon = nysse.styles.load_pictogram_by_mode(self.vehicle_mode)
        if transport_icon is not None:
            transport_icon = pygame.transform.smoothscale(transport_icon, (size[1], size[1])).convert_alpha()

        return transport_icon
