from digitransit.enums import Mode
import pygame
import pygame.surface
import pygame.image

def load_pictogram_by_mode(mode: Mode) -> pygame.surface.Surface:
    lookup = {
        Mode.BUS: "bussi.png",
        Mode.BICYCLE: "kaupunkipyora.png",
        Mode.RAIL: "lahijuna.png",
        Mode.TRAM: "ratikka.png"
    }

    path = lookup[mode] if mode in lookup else "_null.png"
    path = "resources/textures/pictograms/" + path

    surf = pygame.image.load(path).convert_alpha()
    return surf