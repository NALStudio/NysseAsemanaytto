from typing import final
import pygame
from core import config

_instanciated: bool = False

@final
class ElementPositionParams:
    def __init__(self) -> None:
        global _instanciated
        if _instanciated:
            raise RuntimeError(f"{type(self).__name__} is a single-instance class reserved for elements module.")
        _instanciated = True

    @property
    def display_size(self) -> tuple[int, int]:
        # Should be the same as renderer.get_size()
        # which cannot be called due to it creating a circular import.
        return pygame.display.get_window_size()

    @property
    def content_width(self) -> int:
        return self.display_size[0] - (self.display_size[0] // 8)

    @property
    def content_offset(self) -> int:
        return (self.display_size[0] - self.content_width) // 2

    @property
    def content_spacing(self):
        return round(self.content_offset * 0.3)

    @property
    def header_rect(self) -> pygame.Rect:
        return pygame.Rect(self.content_offset, self.content_offset, self.content_width, self.display_size[0] / 13)

    @property
    def stop_info_rect(self) -> pygame.Rect:
        return pygame.Rect(self.content_offset, self.header_rect.bottom + self.content_spacing * 2, self.content_width, self.display_size[0] / 9)

    @property
    def footer_rect(self) -> pygame.Rect:
        footer_height: int = int(self.display_size[0] / 13)
        footer_y: int = self.display_size[1] - self.content_offset - footer_height
        return pygame.Rect(self.content_offset, footer_y, self.content_width, footer_height)

    @property
    def embed_rect(self) -> pygame.Rect:
        last_stoptime_rect: pygame.Rect = self.get_stoptime_rect(config.current.departure_count - 1)
        embed_y: int = round(last_stoptime_rect.y) + last_stoptime_rect.height + (2 * self.content_spacing)
        embed_height: int = self.footer_rect.y - embed_y - self.content_spacing
        return pygame.Rect(0, embed_y, self.display_size[0], embed_height)

    def get_stoptime_rect(self, stoptime_index: int) -> pygame.Rect:
        stoptime_height: int = self.stop_info_rect.height
        stoptime_y_raw: float = self.stop_info_rect.bottom + self.content_spacing + stoptime_index * ((self.content_spacing / 2) + stoptime_height)
        stoptime_y: int = int(stoptime_y_raw)
        return pygame.Rect(self.content_offset, stoptime_y, self.content_width, stoptime_height)

    def get_stoptime_headsign_time_split_x(self, time_font: pygame.font.Font) -> int:
        stoptime_rect = self.get_stoptime_rect(0)
        return stoptime_rect.right - time_font.size("00:00")[0] # 0 should be the widest number in Lato font

    @property
    def stoptime_shortname_headsign_split_x(self) -> int:
        stoptime_rect = self.get_stoptime_rect(0)
        return stoptime_rect.left + stoptime_rect.width // 5
