from digitransit.enums import Mode
import pygame
import pygame.surface
import pygame.image

_pictogram_lookup: dict[Mode, str] = {
    Mode.BUS: "bussi.png",
    Mode.BICYCLE: "kaupunkipyora.png",
    Mode.RAIL: "juna.png",
    Mode.TRAM: "ratikka.png"
}
def load_pictogram_by_mode(mode: Mode, border: bool = False) -> pygame.Surface | None:
    if mode not in _pictogram_lookup:
        return None

    path = _pictogram_lookup[mode]
    border_path_segment: str = "border" if border else "borderless"
    path = f"resources/textures/pictograms/{border_path_segment}/{path}"

    surf = pygame.image.load(path).convert_alpha()
    return surf

_color_lookup: dict[Mode, tuple[int, int, int]] = {
    Mode.BUS: (28, 87, 207),
    Mode.BICYCLE: (104, 66, 171),
    Mode.RAIL: (64, 186, 83),
    Mode.TRAM: (218, 33, 40)
}
def get_color_by_mode(mode: Mode) -> tuple[int, int, int]:
    """Returns (0, 0, 0) if not found."""

    if mode not in _color_lookup:
        return (0, 0, 0)

    return _color_lookup[mode]
