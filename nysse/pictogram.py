from digitransit.enums import Mode
import pygame
import pygame.surface
import pygame.image

def load_pictogram_by_mode(mode: Mode) -> pygame.Surface | None:
    lookup = {
        Mode.BUS: "bussi.png",
        Mode.BICYCLE: "kaupunkipyora.png",
        Mode.RAIL: "juna.png",
        Mode.TRAM: "ratikka.png"
    }

    if mode not in lookup:
        return None

    path = lookup[mode]
    path = "resources/textures/pictograms/" + path

    surf = pygame.image.load(path).convert_alpha()
    return surf
