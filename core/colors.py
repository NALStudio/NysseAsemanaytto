import colorsys as _colorsys

class Colors:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

class NysseColors:
    KESKISININEN = (28, 87, 207)
    TUMMANSININEN = (26, 74, 143)
    VIOLETTI = (104, 66, 171)
    PINKKI = (214, 37, 96)
    VIHREÄ = (14, 127, 60)
    ORANSSI = (235, 94, 71)
    RATIKANPUNAINEN = (218, 33, 40)

def hsv2rgb(hue_deg: float, saturation: float, value: float) -> tuple[int, int, int]:
    """Hue range [0, 360[, Saturation range [0.0, 1.0], Value range [0.0, 1.0]"""
    hue_01: float = (hue_deg % 360.0) / 360.0
    rgb_01: tuple[float, float, float] = _colorsys.hsv_to_rgb(hue_01, saturation, value)

    return tuple(round(i * 255.0) for i in rgb_01)
