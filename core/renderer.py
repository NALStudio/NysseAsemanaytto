import pygame as _pygame
from core import constants as _constants
from core import elements as _elements
from core import debug as _debug
from core import logging as _logging
from nysse import background_generator as _nysse_background
from nalpy import math as _math

_display_surf: _pygame.Surface
_clock: _pygame.time.Clock

_renderers: tuple[_elements.ElementRenderer, ...] = tuple()

_immediate_renders: list[_elements.ElementRenderer] = []
_deferred_renders: list[tuple[_pygame.Surface | None, _pygame.Rect]] = []

_initialized: bool = False
_force_render: bool = False

_background: _pygame.Surface | None = None

_element_position_params: _elements.ElementPositionParams = _elements.ElementPositionParams()

def init(size: tuple[int, int], flags: int):
    global _display_surf, _clock, _initialized

    _pygame.display.set_caption(_constants.APP_DISPLAYNAME)
    _pygame.display.set_icon(_pygame.image.load("resources/textures/icon.png"))

    _display_surf = _pygame.display.set_mode(size, flags)
    _clock = _pygame.time.Clock()

    size_changed()

    _initialized = True


def get_fps(round_to_digits: int | None = None) -> float:
    """Compute the clock framerate (in frames per second) by averaging the last ten calls to `clock.tick()`."""
    fps = _clock.get_fps()
    if round_to_digits is not None:
        fps = _math.round_away_from_zero_to_digits(fps, round_to_digits)
    return fps

def get_frametime(round_to_digits: int | None = None) -> float:
    """
    The number of milliseconds that passed between the previous two calls to `clock.tick()`.
    Includes any time used by `clock.tick()` on delaying to target framerate.
    """
    frametime = _clock.get_time()
    if round_to_digits is not None:
        frametime = _math.round_away_from_zero_to_digits(frametime, round_to_digits)
    return frametime

def get_raw_frametime(round_to_digits: int | None = None) -> float:
    """
    The number of milliseconds that passed between the previous two calls to `clock.tick()`.
    Does not include any time used by `clock.tick()`.
    """
    frametime = _clock.get_rawtime()
    if round_to_digits is not None:
        frametime = _math.round_away_from_zero_to_digits(frametime, round_to_digits)
    return frametime


def get_size() -> tuple[int, int]:
    return _display_surf.get_size()

def get_width() -> int:
    return _display_surf.get_width()

def get_height() -> int:
    return _display_surf.get_height()


def add_renderer(renderer: _elements.ElementRenderer) -> None:
    if _initialized:
        raise RuntimeError("Element Renderers cannot be added after initializing renderer.")

    global _renderers

    _renderers += (renderer,)

def size_changed() -> None:
    global _force_render
    _force_render = True

def update(context: _elements.UpdateContext):
    global _force_render, _background
    forced: bool = _force_render

    for renderer in _renderers:
        if renderer.update(context) or forced:
            _immediate_renders.append(renderer)

    if forced:
        _logging.debug("Forced rendering of background and all display elements.", stack_info=False)
        _background = None
        _force_render = False

def render(framerate: int = -1):
    global _background
    if _background is None:
        _logging.debug("Rendering background...", stack_info=False)
        _background = _nysse_background.generate_background(get_size())
        _display_surf.blit(_background, (0, 0))
        _pygame.display.flip()

    render_rects: list[_pygame.Rect] = []

    for renderer in _immediate_renders:
        rnd: _pygame.Surface | None = renderer.render()
        rect: _pygame.Rect = renderer.get_rect(_element_position_params)

        render_rects.append(rect)
        if _render(rnd, rect, _background, allow_debug=True):
            _deferred_renders.append((rnd, rect))

    for deferred in _deferred_renders:
        rnd: _pygame.Surface | None
        rect: _pygame.Rect
        rnd, rect = deferred

        render_rects.append(rect)
        append_deferred: bool = _render(rnd, rect, _background, allow_debug=False)
        assert append_deferred == False

    _immediate_renders.clear()
    _deferred_renders.clear()

    _pygame.display.update(render_rects)
    _clock.tick(framerate) # clock.tick after update because no time sensitive functionality after display update

def temp_blit(surface: _pygame.Surface, pos: tuple[int, int]):
    _deferred_renders.append((surface, _pygame.Rect(pos, surface.get_size())))

def _render(render: _pygame.Surface | None, rect: _pygame.Rect, background: _pygame.Surface, allow_debug: bool) -> bool:
    _display_surf.blit(background.subsurface(rect), rect.topleft)

    if _debug.enabled == True and allow_debug:
        _pygame.draw.rect(_display_surf, (255, 0, 0), rect.topleft)
        return True

    if render is not None:
        assert render.get_size() == rect.size
        _display_surf.blit(render, rect.topleft)

    return False
