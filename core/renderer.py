import typing as _typing
import pygame as _pygame
import random as _random
import datetime as _datetime
from core import constants as _constants
from core import elements as _elements
from core import debug as _debug
from core import logging as _logging
from nysse import background_generator as _nysse_background
from nalpy import math as _math

class _DeferredRender(_typing.NamedTuple):
    render_time: _datetime.datetime
    surface: _pygame.Surface
    rect: _pygame.Rect
    flags: _elements.RenderFlags
    element_ref: _elements.ElementRenderer
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
_rerender_renders: list[_elements.ElementRenderer] = []

_initialized: bool = False

_background: _pygame.Surface | None = None

def init(size: tuple[int, int], flags: int):
    global _display_surf, _clock, _initialized

    _pygame.display.set_caption(_constants.APP_DISPLAYNAME)
    _pygame.display.set_icon(_pygame.image.load("resources/textures/icon.png"))

    _display_surf = _pygame.display.set_mode(size, flags)
    _clock = _pygame.time.Clock()

    for r in _renderers:
        r.setup()

    force_rerender()

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
    if round_to_digits is not None and not _math.isinf(frametime):
        frametime = _math.round_away_from_zero_to_digits(frametime, round_to_digits)
    return frametime

def get_raw_frametime(round_to_digits: int | None = None) -> float:
    """
    The number of milliseconds that passed between the previous two calls to `clock.tick()`.
    Does not include any time used by `clock.tick()`.
    """
    frametime = _clock.get_rawtime()
    if round_to_digits is not None and not _math.isinf(frametime):
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

def force_rerender(*, rect: _pygame.Rect | None = None, size: tuple[int, int] | None = None, ignore_elements: _typing.Sequence[_elements.ElementRenderer] | None = None) -> None:
    global _rerender_renders, _background

    def should_be_forced(renderer: _elements.ElementRenderer) -> bool:
        if ignore_elements is not None and renderer in ignore_elements:
            return False

        if rect is None or rect.colliderect(renderer.get_rect()):
            return True

        return False

    to_rerender: tuple[_elements.ElementRenderer, ...] = tuple(renderer for renderer in _renderers if should_be_forced(renderer))
    _rerender_renders.extend(to_rerender)

    msg_rnd: list[str] = [f"{len(to_rerender)} display elements."]
    if _background is not None and _background.get_size() != size: # None check provided with !=
        _background = None
        msg_rnd.insert(0, "background")
    _logging.debug(f"Forced rendering of {' and '.join(msg_rnd)}.", stack_info=False)

def update(context: _elements.UpdateContext):
    global _background

    for renderer in _renderers:
        if renderer.update(context):
            _immediate_renders.append(renderer)

def render(now: _datetime.datetime, framerate: int = -1):
    global _background, _immediate_renders, _rerender_renders
    if _background is None:
        _logging.debug("Rendering background...", stack_info=False)
        _background = _nysse_background.generate_background(get_size())
        _display_surf.blit(_background, (0, 0))
        _pygame.display.flip()

    render_rects: list[_pygame.Rect] = []
    render_rects.extend(_render_immediate(now, _background))

    rerender_iterations: int = 0
    while len(_rerender_renders) > 0:
        if rerender_iterations >= 10:
            raise RuntimeError("maximum rerender recursion depth reached.")

        _immediate_renders.extend(rerender for rerender in _rerender_renders)
        _rerender_renders.clear()
        render_rects.extend(_render_immediate(now, _background))

        rerender_iterations += 1

    render_rects.extend(_render_deferred(now, _background))

    _debug.set_custom_field("render_count", "Render Count", len(render_rects))
    _pygame.display.update(render_rects)
    _clock.tick(framerate) # clock.tick after update because no time sensitive functionality after display update

def _render_immediate(now: _datetime.datetime, background: _pygame.Surface) -> _typing.Iterator[_pygame.Rect]:
    global _deferred_renders, _immediate_renders
    for renderer in _immediate_renders:
        flags: _elements.RenderFlags = _elements.RenderFlags()
        rect: _pygame.Rect = renderer.get_rect()
        rnd: _pygame.Surface | None = renderer.render(rect.size, flags)
        debug_col: tuple[int, int, int] = _get_debug_color(renderer)
        if _render(rnd, rect, flags, renderer, background, True, debug_col) and rnd is not None:
            scheduled: _DeferredRender = _DeferredRender(now + _datetime.timedelta(seconds=0.2), rnd, rect, flags, renderer, debug_col)
            _deferred_renders.append(scheduled)
        yield rect

    _immediate_renders.clear()

def _render_deferred(now: _datetime.datetime, background: _pygame.Surface) -> _typing.Iterator[_pygame.Rect]:
    global _deferred_renders
    for deferred in _deferred_renders.copy():
        if deferred.render_time > now: # If still in future
            continue

        _deferred_renders.remove(deferred)
        append_deferred: bool = _render(deferred.surface, deferred.rect, deferred.flags, deferred.element_ref, background, False, deferred.debug_color)
        assert append_deferred == False

        yield deferred.rect

def _clear_background(rect: _pygame.Rect, background: _pygame.Surface, debug_color: tuple[int, int, int]):
    bkgrnd: _pygame.Surface = background.subsurface(rect.clip((0, 0, *background.get_size())))
    if _debug.rect_enabled:
        debug_bkgrnd = _pygame.Surface(rect.size)
        debug_bkgrnd.fill(debug_color)
        bkgrnd = debug_bkgrnd

    _display_surf.blit(bkgrnd, rect.topleft)

def _render(render: _pygame.Surface | None, rect: _pygame.Rect, flags: _elements.RenderFlags, element_ref: _elements.ElementRenderer, background: _pygame.Surface, allow_debug: bool, debug_color: tuple[int, int, int]) -> bool:
    if flags.clear_background:
        _clear_background(rect, background, debug_color)
    if flags.rerender_colliding_elements:
        force_rerender(rect=rect, size=get_size(), ignore_elements=(element_ref,))

    if _debug.render_enabled == True and allow_debug:
        render_update_debug_col: tuple[int, int, int] = (255, 0, 0) if flags.clear_background else (0, 0, 255)
        _pygame.draw.rect(_display_surf, render_update_debug_col, rect)
        return True

    if render is not None:
        assert render.get_size() == rect.size
        _display_surf.blit(render, rect.topleft)

    return False
