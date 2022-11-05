from nalpy import math
from core import logging, testing
from typing import Iterable, NamedTuple
import pygame

class SizedFont:
    def __init__(self, path: str, purpose: str | None = None) -> None:
        self._path: str = path
        self._loaded_size: int | None = None
        self._font: pygame.font.Font | None = None

        self._purpose: str | None = purpose

    def get_size(self, size: int) -> pygame.font.Font:
        if self._font is None or size != self._loaded_size:
            if self._purpose is not None:
                logging.debug(f"Loading new font for {self._purpose}...", stack_info=False)

            self._loaded_size = size
            self._font = pygame.font.Font(self._path, size)

        return self._font


def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> Iterable[str]:
    """
    Wrap text to fit within a maximum width.
    """

    WORD_BOUNDARY = " "

    line: str | None = None
    for word in text.split(WORD_BOUNDARY):
        if line is not None and font.size(line + WORD_BOUNDARY + word)[0] > max_width:
            yield line
            line = word
        elif line is None:
            line = word
        else:
            line += WORD_BOUNDARY + word

    if line is not None and len(line) > 0:
        yield line


class Page(NamedTuple):
    index: int
    size: tuple[int, int]
    lines: tuple[str, ...]

def pagination(font: pygame.font.Font, text: str, page_size: tuple[int, int]) -> Iterable[Page]:
    """
    Split text into pages.
    """

    lines: list[str] = list(wrap_text(font, text, page_size[0]))

    lines_per_page: int = math.floor(page_size[1] / font.get_linesize())

    for i in range(0, len(lines), lines_per_page):
        page_index = int(i / lines_per_page)
        page_lines = tuple(lines[i:i + lines_per_page])
        yield Page(page_index, page_size, page_lines)

def render_page(font: pygame.font.Font, page: Page, antialias: bool, color: tuple[int, int, int], background: tuple[int, int, int] | None = None) -> pygame.Surface:
    def render_generator() -> Iterable[tuple[pygame.Surface, tuple[int, int]]]:
        linesize: int = font.get_linesize()

        for i, line in enumerate(page.lines):
            render = font.render(line, antialias, color, background)
            y: int = i * linesize
            yield render, (0, y)

    # faster to create an alpha surface than a non-alpha surface with filled background
    surf: pygame.Surface = pygame.Surface(page.size, pygame.SRCALPHA)
    surf.blits(list(render_generator()))

    return surf
