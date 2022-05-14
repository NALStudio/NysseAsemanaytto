from __future__ import annotations as _annotations

from time import time as _time
import typing as _typing
from core import math as _math
from core import console_utils as _console_utils

class SpinnerStyle(_typing.NamedTuple):
    frames: _typing.Sequence[str] = ('◷', '◶', '◵', '◴')
    frame_length: float = 0.25
    hide_cursor: bool = True

    @classmethod
    @property
    def default(cls) -> SpinnerStyle:
        return SpinnerStyle()

class Spinner:
    def __init__(self, style: SpinnerStyle) -> None:
        self._style: SpinnerStyle = style
        self._starttime: float | None = None
        self._cursor_hidden: bool = False

    def __enter__(self) -> Spinner:
        self.start()
        return self

    def __exit__(self, *_) -> bool:
        self.stop()
        return False

    def start(self):
        if self._style.hide_cursor:
            _console_utils.cursor_hide()
            self._cursor_hidden = True
        self._starttime = _time()

    def update(self, message: str) -> float:
        """Updates the spinner

        Returns:
            float: The elapsed seconds
        """
        if self._starttime is None:
            raise RuntimeError("Spinner has to be started before updating!")

        elapsed_seconds = _time() - self._starttime
        frame_index: int = int(elapsed_seconds // self._style.frame_length)
        frame_index %= len(self._style.frames)

        _console_utils.carriage_return()
        print(self._style.frames[frame_index], end=" ")
        print(message, end="")

        return elapsed_seconds

    def stop(self) -> None:
        """Resets the cursor visibility if it was modified."""
        if self._cursor_hidden:
            _console_utils.cursor_show()
            self._cursor_hidden = False
