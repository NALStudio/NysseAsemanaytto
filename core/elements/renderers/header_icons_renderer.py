import pygame
from core import elements, render_info
import nysse.styles
import digitransit.enums

class HeaderIconsRenderer(elements.ElementRenderer):
    def __init__(self) -> None:
        assert render_info.stopinfo.vehicleMode is not None
        self.vehicle_mode: digitransit.enums.Mode = render_info.stopinfo.vehicleMode

    def update(self, context: elements.UpdateContext) -> bool:
        if render_info.stopinfo.vehicleMode is not None and self.vehicle_mode != render_info.stopinfo.vehicleMode:
            self.vehicle_mode = render_info.stopinfo.vehicleMode
            return True

        return False

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        header_rect: pygame.Rect = params.header_rect
        return pygame.Rect(header_rect.left, header_rect.top, header_rect.height, header_rect.height) # width is height, square

    def render(self, rect: pygame.Rect) -> pygame.Surface | None:
        transport_icon = nysse.styles.load_pictogram_by_mode(self.vehicle_mode)
        if transport_icon is not None:
            transport_icon = pygame.transform.smoothscale(transport_icon, (rect.height, rect.height)).convert_alpha()

        return transport_icon
