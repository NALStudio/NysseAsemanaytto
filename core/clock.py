# interesting pull: https://github.com/pygame/pygame/pull/2411
import pygame.time as _time

from core import math as _math


#region Tested custom clock because pygame clock is inaccurate, but didn't seem to help
# class CustomClock:
#     def __init__(self) -> None:
#         self._perfcounter: int = time.perf_counter_ns()
#         self.last_ten_diffs: list[int] = [math.MAXVALUE for _ in range(10)]
#
#     def tick(self, framerate: int = 0) -> float:
#         if framerate > 0:
#             raise NotImplementedError()
#
#         while len(self.last_ten_diffs) > 9:
#             self.last_ten_diffs.pop(0)
#
#         old = self._perfcounter
#         self._perfcounter = time.perf_counter_ns()
#         diff = self._perfcounter - old
#
#         self.last_ten_diffs.append(diff)
#
#         return diff / 1_000_000
#
#     def get_fps(self) -> float:
#         frames = len(self.last_ten_diffs)
#         assert frames == 10
#
#         nanoseconds = sum(self.last_ten_diffs)
#         seconds = nanoseconds / 1_000_000_000
#
#         return frames / seconds
#endregion


_clock = _time.Clock()
delta_time: float = 1.0

def tick(framerate: int = 0):
    """
    This method should be called once per frame. It will compute deltatime which determines how many seconds have passed since the previous call.

    If you pass the optional framerate argument the function will delay to keep the game running slower than the given ticks per second.
    This can be used to help limit the runtime speed of a game.
    By calling Clock.tick(40) once per frame, the program will run at approximately 40 frames per second.

    """
    global delta_time
    milliseconds = _clock.tick(framerate)
    delta_time = milliseconds / 1000

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

def sleep(seconds: float): # Using seconds to future-proof this in-case we switch clocks to nanosecond accuracy etc.
    """
    Pause the program for an amount of time.

    Seconds are rounded to milliseconds.
    """
    _time.wait(round(seconds * 1000))

def delay(seconds: float):
    """
    Pause the program for an amount of time.

    Seconds are rounded to milliseconds.
    """
    _time.delay(round(seconds * 1000))
