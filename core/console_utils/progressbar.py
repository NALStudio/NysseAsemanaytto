from __future__ import annotations as _annotations

import typing as _typing

from core import math as _math
from core import console_utils as _console_utils


class ProgressbarStyle(_typing.NamedTuple):
    width: int = 32
    bar_prefix: str = ' '
    bar_suffix: str = ' '
    empty_fill: str = '∙'
    fill: str = '█'
    color: _console_utils.ConsoleColor | None = None
    hide_cursor: bool = True

    @classmethod
    @property
    def default(cls) -> ProgressbarStyle:
        return ProgressbarStyle()

class Progressbar:
    def __init__(self, style: ProgressbarStyle) -> None:
        self._style: ProgressbarStyle = style
        self._cursor_hidden: bool = False

    def __enter__(self) -> Progressbar:
        self.start()
        return self

    def __exit__(self, *_) -> bool:
        self.stop()
        return False

    def start(self):
        """Hides the cursor if it is requested by style"""
        if self._style.hide_cursor:
            _console_utils.cursor_hide()
            self._cursor_hidden = True

    def update(self, message: str, progress: float, _min: float = 0.0, _max: float = 1.0) -> None:
        t = _math.clamp01(_math.remap01(progress, _min, _max))
        filled_length = int(self._style.width * t)
        empty_length = self._style.width - filled_length

        bar = self._style.fill * filled_length
        empty = self._style.empty_fill * empty_length
        suffix = f"{round(t * 100)}%"

        _console_utils.carriage_return()
        print(message, self._style.bar_prefix, sep="", end="")
        if self._style.color is not None:
            _console_utils.set_foreground_color(self._style.color)
        print(bar, end="")
        _console_utils.reset_attributes()
        print(empty, self._style.bar_suffix, suffix, sep="", end="")

    def stop(self) -> None:
        """Resets the cursor visibility if it was modified."""
        if self._cursor_hidden:
            _console_utils.cursor_show()
            self._cursor_hidden = False