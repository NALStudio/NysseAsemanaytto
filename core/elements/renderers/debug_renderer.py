import os
import threading
import psutil
import pygame
from core import debug, elements, renderer, font_helper
from core.colors import Colors

class DebugRenderer(elements.ElementRenderer):
    def __init__(self) -> None:
        self.last_debug: bool = False
        self.debug: bool = False
        self.render_empty: bool = False
        self.render_fields: list[str] = []

    def setup(self) -> None:
        self.font: pygame.font.Font = pygame.font.Font("resources/fonts/Lato-Regular.ttf", 14)

    def update(self, context: elements.UpdateContext) -> bool:
        self.last_debug = self.debug
        self.debug = debug.enabled

        if self.debug:
            self.render_fields = self._prepare_fields()
        if self.render_empty: # Force render after rendering debug empty
            renderer.force_render()
            self.render_fields = []
        self.render_empty = self.debug == False and self.last_debug == True

        return self.debug or self.last_debug # Last debug ensures one call after debug is disabled

    def _prepare_fields(self) -> list[str]:
        memory_usage_msg: str = "disabled"
        thread_count_msg: str = "disabled"

        thread_fields: list[tuple[str, object]] = []
        if debug.process_enabled:
            process = psutil.Process(os.getpid())
            memory_full_info = process.memory_full_info()
            memory_usage_msg = f"{memory_full_info.uss / 1_048_576:.1f} MB ({(memory_full_info.rss / psutil.virtual_memory().available) * 100:.1f} %)"

            for thread in threading.enumerate():
                thread_fields.append((f"    {thread.name}", thread.ident))
            thread_count_msg = str(len(thread_fields))

        fields: list[tuple[str, object]] = debug.get_fields(
            ("Frametime", f"{renderer.get_frametime(3):.2f} ms"),
            ("Raw Frametime", f"{renderer.get_raw_frametime(3):.2f} ms"),
            ("Memory Usage", memory_usage_msg),
            (f"Threads", thread_count_msg),
            *thread_fields
        )

        return [f"{name}: {value}" for name, value in fields]

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        width: int = round(params.display_size[0] / 3)
        height: int = len(self.render_fields) * self.font.get_linesize()

        return pygame.Rect(0, 0, width, height)

    def render(self, size: tuple[int, int]) -> pygame.Surface | None:
        if self.render_empty:
            return None

        surf: pygame.Surface = pygame.Surface(size)
        for i, field in enumerate(self.render_fields):
            rendered_field: pygame.Surface = self.font.render(field, True, Colors.WHITE)
            surf.blit(rendered_field, (0, i * self.font.get_linesize()))

        return surf
