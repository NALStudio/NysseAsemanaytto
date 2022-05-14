# More secure than Log4j!

import inspect as _inspect
import logging as _logger
import os as _os
import platform as _platform
import traceback as _traceback
import psutil as _psutil
import pygame as _pygame

from sys import version_info as _python_version
from datetime import datetime as _datetime
from core import console_utils as _console_utils

LOGGING_DIRECTORY = "./logs"

_logfile_time_format: str = "%Y-%m-%d-%H-%M-%S"

_logfile_prefix: str = "log_"
_logfile_extension: str = ".log"

_crashfile_prefix: str = "crash_"
_crashfile_extension: str = ".fuck"

_logentry_format: str = "%(levelname)s-%(asctime)s: %(message)s"
_logentry_time_format: str = "%H:%M:%S"

_loglevel_colors: dict[int, tuple[_console_utils.ConsoleColor, bool]] = {
    _logger.DEBUG: (_console_utils.ConsoleColor.GREEN, False),
    _logger.INFO: (_console_utils.ConsoleColor.BLUE, False),
    _logger.WARNING: (_console_utils.ConsoleColor.YELLOW, False),
    _logger.ERROR: (_console_utils.ConsoleColor.RED, False),
    _logger.CRITICAL: (_console_utils.ConsoleColor.DARK_RED, True)
}

def _validate_logfilelike_name(filename: str, expected_extension: str, expected_prefix: str) -> _datetime | None:
    split = _os.path.splitext(filename)
    if len(split) < 2 or split[1] != expected_extension:
        return None

    if not split[0].startswith(expected_prefix):
        return None

    dt: _datetime | None
    try:
        dt = _datetime.strptime(split[0].removeprefix(expected_prefix), _logfile_time_format)
    except Exception:
        dt = None
    return dt

def _validate_logfile_name(filename: str) -> _datetime | None:
    """
    Validates logfile name and gets the datetime associated with it.

    Returns None if invalid
    """
    return _validate_logfilelike_name(filename, _logfile_extension, _logfile_prefix)

def _validate_crashfile_name(filename: str) -> _datetime | None:
    return _validate_logfilelike_name(filename, _crashfile_extension, _crashfile_prefix)

def init():
    # Create log directory if it doesn't exist
    _os.makedirs(LOGGING_DIRECTORY, exist_ok=True)

    #region Create new log file
    logtime: str = _datetime.now().strftime(_logfile_time_format)
    filename = _os.path.join(LOGGING_DIRECTORY, f"{_logfile_prefix}{logtime}{_logfile_extension}")
    _logger.basicConfig(filename=filename, format=_logentry_format, level=_logger.NOTSET, datefmt=_logentry_time_format)
    debug(f"Created log file: {filename}", console_visible=False, stack_info=False)
    #endregion

    #region Remove old log files
    logfiles: list[str] = _os.listdir(LOGGING_DIRECTORY)
    valid_files: list[tuple[_datetime, str]] = []
    crash_file_count: int = 0
    for logfile in logfiles:
        dt: _datetime | None = _validate_logfile_name(logfile)
        if dt is not None:
            valid_files.append((dt, logfile))
        elif _validate_crashfile_name(logfile) is not None:
            crash_file_count += 1

    logfiles_to_delete: list[tuple[_datetime, str]] = list(sorted(valid_files, key=lambda dp: dp[0], reverse=True))[5:]
    for _, to_delete in logfiles_to_delete:
        whole_path = _os.path.join(LOGGING_DIRECTORY, to_delete)
        try:
            _os.remove(whole_path)
        except Exception as e:
            critical(e)
            warning(f"Could not remove logfile: '{whole_path}'")

    if crash_file_count > 16:
        warning(f"Found {crash_file_count} crash dumps in '{LOGGING_DIRECTORY}'.\nConsider clearing out some unused ones.", stack_info=False)
    #endregion


def dump_crash_exception(exception: Exception) -> None:
    """Dumps the crash exception into a file"""
    crashtime: str = _datetime.now().strftime(_logfile_time_format)
    filename = _os.path.join(LOGGING_DIRECTORY, f"{_crashfile_prefix}{crashtime}{_crashfile_extension}")
    exc: list[str]
    try:
        exc = _traceback.format_exception(type(exception), exception, exception.__traceback__)
    except Exception as e:
        exc = [
            "[DUMP ERROR]: Could not format exception.",
           f"Got error: '{type(e).__name__}' with message: '{e}' during formatting.",
           f"Got error: '{type(exception).__name__}' with message: '{exception}' during application execution."
        ]

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(exc)


def print_display_debug_info():
    display_info = _pygame.display.Info()
    mixer_version = _pygame.mixer.get_sdl_mixer_version(True)
    platform_info = _platform.uname()
    memory_info = _psutil.virtual_memory()
    debug(f"""\nI=====[ DEBUG INFO ]=====I
    [Version Info]
    - pygame: {_pygame.version.ver}
    - SDL: {_pygame.version.SDL.major}.{_pygame.version.SDL.minor}.{_pygame.version.SDL.patch}
    - SDL Mixer: {mixer_version[0]}.{mixer_version[1]}.{mixer_version[2]}
    - Python: {_python_version.major}.{_python_version.minor}.{_python_version.micro}
    - {platform_info.system} {platform_info.release}: {platform_info.version}

    [Video Info]
    - SDL Video Driver: {_pygame.display.get_driver()}
    - Hardware Acceleration: {bool(display_info.hw)}
    - Window Allowed: {bool(display_info.wm)}
    - Video Memory: {display_info.video_mem if display_info.video_mem != 0 else "N/A"}

    [Pixel Info]
    - Bit Size: {display_info.bitsize}
    - Byte Size: {display_info.bytesize}
    - Masks: {display_info.masks}
    - Shifts: {display_info.shifts}
    - Losses: {display_info.losses}

    [System Info]
    - Architecture: {platform_info.machine}
    - Processor (Cores: {_psutil.cpu_count(logical=False)}, Threads: {_psutil.cpu_count(logical=True)}): {platform_info.processor}
    - RAM: {memory_info.available / 1_073_741_824} GB Available ({memory_info.total / 1_073_741_824} GB Total)

    [Hardware Acceleration]
    - Hardware Blitting: {bool(display_info.blit_hw)}
    - Hardware Colorkey Blitting: {bool(display_info.blit_hw_CC)}
    - Hardware Pixel Alpha Blitting: {bool(display_info.blit_hw_A)}
    - Software Blitting: {bool(display_info.blit_sw)}
    - Software Colorkey Blitting: {bool(display_info.blit_sw_CC)}
    - Software Pixel Alpha Blitting: {bool(display_info.blit_sw_A)}\nI=====[ DEBUG INFO ]=====I""",
    console_visible=False, stack_info=False)


def _log(message: str | Exception, console_visible: bool, stack_info: bool, log_level: int) -> None:
    frameinfo = _inspect.getouterframes(_inspect.currentframe(), 2)[2]

    exc: Exception | None = None
    if isinstance(message, Exception):
        exc = message
        message = f"{type(message).__name__}: {str(message)}"

    _logger.log(log_level, message, exc_info=exc, stack_info=stack_info, stacklevel=4)
    if console_visible:
        console_message: list[str] = message.splitlines()
        if stack_info:
            console_message = [f"    {line}" for line in console_message]
            console_message.insert(0, f"File \"{frameinfo.filename}\", line {frameinfo.lineno}, in {frameinfo.function}")
            console_message.append("    Read log file for more details.")

        color, colorize_text = _loglevel_colors[log_level]
        _console_utils.set_background_color(color)
        prefix = f"[ {_logger.getLevelName(log_level)} ]"
        print(prefix, end="")
        _console_utils.reset_attributes()
        if colorize_text:
            _console_utils.set_foreground_color(color)
        print(" ", end="")
        print(*console_message, sep="\n" + " " * (len(prefix) + 1), end="")
        _console_utils.reset_attributes()
        print()

def debug(message: str | Exception, console_visible: bool = True, stack_info: bool = True) -> None:
    _log(message, console_visible, stack_info, _logger.DEBUG)

def info(message: str | Exception, console_visible: bool = True, stack_info: bool = True) -> None:
    _log(message, console_visible, stack_info, _logger.INFO)

def warning(message: str | Exception, console_visible: bool = True, stack_info: bool = True) -> None:
    _log(message, console_visible, stack_info, _logger.WARNING)

def error(message: str | Exception, console_visible: bool = True, stack_info: bool = True) -> None:
    _log(message, console_visible, stack_info, _logger.ERROR)

def critical(exception: str | Exception, console_visible: bool = True, stack_info: bool = True) -> None:
    _log(exception, console_visible, stack_info, _logger.CRITICAL)

def quit():
    _logger.shutdown()
