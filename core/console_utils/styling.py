from core.console_utils import ConsoleColor, ConsoleStyle
from core.console_utils.commands import _set_csi

# NOTE: Remember to add to console_utils public imports

def _get_ansi_color(color: ConsoleColor, prefix_number: int) -> str:
    suffix = ""
    number = color.value
    if number >= 10:
        suffix = ";1"
        number -= 10

    return f"{prefix_number}{number}{suffix}"

def _set_sgr(command: str):
    _set_csi(command + "m")

def set_foreground_color(color: ConsoleColor):
    ansi = _get_ansi_color(color, prefix_number=3)
    _set_sgr(ansi)

def set_background_color(color: ConsoleColor): # NOTE: This leaves a long colored line in VSCode for some reason
    ansi = _get_ansi_color(color, prefix_number=4)
    _set_sgr(ansi)

def set_style(style: ConsoleStyle):
    _set_sgr(str(style))

def reset_attributes():
    _set_sgr("0")