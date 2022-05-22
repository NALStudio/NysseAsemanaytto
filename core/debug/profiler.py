from cProfile import Profile as _Profile
import pstats as _pstats
from io import StringIO as _StringIO
from core import logging as _logging

_profiler: _Profile | None = None

def is_enabled():
    global _profiler
    return _profiler is not None

def enable():
    global _profiler
    if _profiler is not None:
        _logging.warning("Profiler is already enabled. Restarting profiler...")
        _profiler.disable()

    _profiler = _Profile()
    _profiler.enable()


def disable():
    global _profiler

    if _profiler is None:
        _logging.warning("Profiler is already disabled. Ignoring disable request...")
        return

    _profiler.disable()
    internal_profiler = _profiler
    _profiler = None

    stats: str
    with _StringIO() as s:
        ps = _pstats.Stats(internal_profiler, stream=s)
        ps.strip_dirs().sort_stats(_pstats.SortKey.CUMULATIVE)
        ps.print_stats()
        s.seek(0)
        stats = s.read()

    message_lines = (
        "",
        "I=========================[ EXPORTED PROFILER DATA ]=========================I",
        "",
        stats,
        "I=========================[ EXPORTED PROFILER DATA ]=========================I",
    )

    _logging.debug("\n".join(message_lines), stack_info=False)