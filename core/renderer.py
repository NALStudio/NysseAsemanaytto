from typing import NamedTuple as _NamedTuple
import pygame as _pygame
import random as _random
import datetime as _datetime
from core import constants as _constants
from core import elements as _elements
from core import debug as _debug
from core import logging as _logging
from nysse import background_generator as _nysse_background
from nalpy import math as _math

class _DeferredRender(_NamedTuple):
    render_time: _datetime.datetime
    surface: _pygame.Surface
    rect: _pygame.Rect
    debug_color: tuple[int, int, int]

_display_surf: _pygame.Surface
_clock: _pygame.time.Clock

_renderers: tuple[_elements.ElementRenderer, ...] = tuple()
_renderer_debug_colors: dict[_elements.ElementRenderer, tuple[int, int, int]] = {}
def _get_debug_color(renderer: _elements.ElementRenderer) -> tuple[int, int, int]:
    if renderer not in _renderer_debug_colors:
        debug_color = (_random.randint(0, 255), _random.randint(0, 255), _random.randint(0, 255))
        _renderer_debug_colors[renderer] = debug_color

    return _renderer_debug_colors[renderer]

def reset_debug_colors() -> None:
    _renderer_debug_colors.clear()

_immediate_renders: list[_elements.ElementRenderer] = []
_deferred_renders: list[_DeferredRender] = []

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

    for r in _renderers:
        r.setup()

    force_render()

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

    global _renderers, _renderer_debug_colors

    if renderer in _renderers:
        raise ValueError("Renderer has been added already.")

    _renderers += (renderer,)

def force_render() -> None:
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

def render(now: _datetime.datetime, framerate: int = -1):
    global _background
    if _background is None:
        _logging.debug("Rendering background...", stack_info=False)
        _background = _nysse_background.generate_background(get_size())
        _display_surf.blit(_background, (0, 0))
        _pygame.display.flip()

    render_rects: list[_pygame.Rect] = []

    for renderer in _immediate_renders:
        rect: _pygame.Rect = renderer.get_rect(_element_position_params)
        rnd: _pygame.Surface | None = renderer.render(rect.size)
        debug_col: tuple[int, int, int] = _get_debug_color(renderer)
        render_rects.append(rect)
        if _render(rnd, rect, _background, True, debug_col) and rnd is not None:
            scheduled: _DeferredRender = _DeferredRender(now + _datetime.timedelta(seconds=0.2), rnd, rect, debug_col)
            _deferred_renders.append(scheduled)

    _immediate_renders.clear()

    for deferred in _deferred_renders.copy():
        if deferred.render_time > now: # If still in future
            continue

        _deferred_renders.remove(deferred)
        render_rects.append(deferred.rect)
        append_deferred: bool = _render(deferred.surface, deferred.rect, _background, False, deferred.debug_color)
        assert append_deferred == False

    _pygame.display.update(render_rects)
    _clock.tick(framerate) # clock.tick after update because no time sensitive functionality after display update

def temp_blit(surface: _pygame.Surface, pos: tuple[int, int]):
    rect = _pygame.Rect(pos, surface.get_size())
    timestamp = _datetime.datetime.fromtimestamp(0.0)
    deferred = _DeferredRender(timestamp, surface, rect, (0, 255, 255))
    _deferred_renders.append(deferred)

def _render(render: _pygame.Surface | None, rect: _pygame.Rect, background: _pygame.Surface, allow_debug: bool, debug_color: tuple[int, int, int]) -> bool:
    bkgrnd: _pygame.Surface = background.subsurface(rect)
    if _debug.rect_enabled:
        debug_bkgrnd = _pygame.Surface(rect.size)
        debug_bkgrnd.fill(debug_color)
        bkgrnd = debug_bkgrnd

    _display_surf.blit(bkgrnd, rect.topleft)

    if _debug.render_enabled == True and allow_debug:
        _pygame.draw.rect(_display_surf, (255, 0, 0), rect)
        return True

    if render is not None:
        assert render.get_size() == rect.size
        _display_surf.blit(render, rect.topleft)

    return False
