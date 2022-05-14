from core.console_utils.commands import _set_csi

# NOTE: Remember to add to console_utils public imports

def _set_seq(value: int, suffix: str):
    _set_csi(f"{value}{suffix}")


def cursor_up(count: int = 1):
    _set_seq(count, "A")

def cursor_down(count: int = 1):
    _set_seq(count, "B")

def cursor_forward(count: int = 1):
    _set_seq(count, "C")

def cursor_back(count: int = 1):
    _set_seq(count, "D")

def cursor_line_down(count: int = 1):
    _set_seq(count, "E")

def cursor_line_up(count: int = 1):
    _set_seq(count, "F")

def cursor_set_column(column_index: int):
    """columns are 1-based."""
    _set_seq(column_index, "G")

def cursor_set_pos(row_index: int, column_index: int):
    """rows and columns are 1-based"""
    _set_csi(f"{row_index};{column_index}H")


def cursor_hide():
    _set_csi("?25l")

def cursor_show():
    _set_csi("?25h")


def _erase_display(mode: int):
    _set_seq(mode, "J")

def clear():
    """Clear the entire screen and move to upperleft."""
    _erase_display(2)
    cursor_set_pos(1, 1)

def lclear():
    """Clear from cursor to the beginning of the screen."""
    _erase_display(1)

def rclear():
    """Clear from cursor to the end of screen."""
    _erase_display(0)

def _erase_line(mode: int):
    _set_seq(mode, "K")

def erase():
    """Clear the entire line."""
    _erase_line(2)

def lerase():
    """Clear from cursor to beginning of the line."""
    _erase_line(1)

def rerase():
    """Clear from cursor to the end of the line."""
    _erase_line(0)


def scroll_up(lines: int):
    _set_seq(lines, "S")

def scroll_down(lines: int):
    _set_seq(lines, "T")


def cursor_get_pos() -> tuple[int, int]:
    raise NotImplementedError()
