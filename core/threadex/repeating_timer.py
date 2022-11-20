import random
import string
from typing import Any, Callable, ParamSpec
from threading import Timer, Thread
from core import threadex

P = ParamSpec("P")

class RepeatingTimer:
    def __init__(self, name_prefix: str, interval: float, function: Callable[P, None], *args: P.args, **kwargs: P.kwargs) -> None:
        self._prefix: str = name_prefix
        self._interval: float = interval

        self._function: Callable = function
        self._args: tuple[Any, ...] = args
        self._kwargs: dict[str, Any] = kwargs

        self._daemon: bool = False
        self._timer: Timer | None = None

        self._running: bool = False

    def start(self) -> None:
        self._running = True

        assert self._timer is None
        self._timer = self._create_timer()
        self._timer.start()

    def start_immediate(self) -> None:
        self._running = True
        self._run(join_func_thread=False)

    def start_synchronous(self) -> None:
        self._running = True
        self._run(join_func_thread=True)

    def cancel(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self._running = False

    def _run(self, *, join_func_thread: bool = False) -> None:
        func_thread: Thread = Thread(target=self._function, name=self._generate_thread_name(suffix_override="call"), args=self._args, kwargs=self._kwargs, daemon=self._daemon)
        func_thread.start()
        if join_func_thread:
            func_thread.join()

        self._timer = self._create_timer()
        self._timer.start()

    def is_alive(self) -> bool:
        if self._running:
            return True

        if self._timer is None:
            return False

        return self._timer.is_alive()

    def _create_timer(self) -> Timer:
        t = Timer(self._interval, self._run)
        t.daemon = self._daemon
        t.name = self._generate_thread_name()
        return t

    def _generate_thread_name(self, *, suffix_override: str | None = None) -> str:
        if suffix_override is not None:
            return threadex.thread_names.name_with_suffix(self._prefix, suffix_override)
        else:
            return threadex.thread_names.name_with_identifier(self._prefix)
