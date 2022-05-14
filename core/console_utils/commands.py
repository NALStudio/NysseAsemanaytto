# NOTE: Remember to add to console_utils public imports

def _set_control(command: str):
    print(command, end="")

def _set_csi(command: str):
    _set_control("\u001B[" + command)

def bell():
    """Makes an audible noise."""
    _set_control("\u0007")

def backspace():
    """Moves the cursor one left to enable overwriting of following characters."""
    _set_control("\u0008")

def tab():
    _set_control("\u0009")

def line_feed():
    """Moves to next line, scrolls the display up if at bottom of the screen."""
    _set_control("\u000A")

def form_feed():
    """Move a printer to top of next page."""
    _set_control("\u000C")

def carriage_return():
    """Moves the cursor to column zero."""
    _set_control("\u000D")