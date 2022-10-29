from typing import Final, Self
from datetime import timedelta
from time import perf_counter_ns

NANOSECOND_TO_MILLISECOND: Final[float] = 1 / 1000000 # 0,000001

class Stopwatch():
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._start_timestamp_ns: int | None = None
        self._elapsed: int = 0

    @classmethod
    def start_new(cls) -> Self:
        sw = cls()
        sw.start()
        return sw

    def start(self):
        if self._start_timestamp_ns is not None:
            return

        self._start_timestamp_ns = perf_counter_ns()

    def stop(self):
        if self._start_timestamp_ns is None:
            return

        end_timestamp_ns = perf_counter_ns()
        elapsed_this_period_ns: int = end_timestamp_ns - self._start_timestamp_ns
        self._elapsed += elapsed_this_period_ns
        self._start_timestamp_ns = None

    def restart(self) -> None:
        self.reset()
        self.start()

    @property
    def is_running(self) -> bool:
        return self._start_timestamp_ns is not None

    @property
    def elapsed(self) -> timedelta:
        return timedelta(milliseconds=self.elapsed_milliseconds)

    @property
    def elapsed_milliseconds(self) -> float:
        return self.elapsed_nanoseconds * NANOSECOND_TO_MILLISECOND

    @property
    def elapsed_nanoseconds(self) -> int:
        return self._get_elapsed_nanoseconds()

    def _get_elapsed_nanoseconds(self) -> int:
        time_elapsed: int = self._elapsed

        if self._start_timestamp_ns is not None: # timer is running
            current_timestamp: int = perf_counter_ns()
            elapsed_until_now: int = current_timestamp - self._start_timestamp_ns
            time_elapsed += elapsed_until_now

        return time_elapsed







