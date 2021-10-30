import pygame
import pygame.image
import pygame.surface
import pygame.transform
from core.colors import Colors
from digitransit.enums import Mode
from typing import Optional, Tuple

font: Optional[pygame.font.Font] = None
font_height: Optional[int] = None
nyssefi_text: Optional[pygame.surface.Surface] = None

footer_pictograms: Optional[pygame.surface.Surface] = None

def renderFooter(px_size: Tuple[int, int]) -> pygame.Surface:
    global font, font_height, footer_pictograms, nyssefi_text
    target_font_height: int = px_size[1]
    if font == None or target_font_height != font_height or nyssefi_text == None:
        print("Loading new font for stop info rendering...")
        font_height = target_font_height
        font = pygame.font.Font("resources/fonts/Lota-Grotesque-Bold.otf", font_height)
        nyssefi_text = font.render("nysse.fi", True, Colors.WHITE)

    footer_pictograms_height: float = px_size[1] * 0.7
    if footer_pictograms == None or footer_pictograms.get_height() != round(footer_pictograms_height):
        print("Loading new pictograms for footer...")
        footer_pictograms = pygame.image.load("resources/textures/elements/footer/footer_pictograms.png")
        footer_pictograms_width: float = footer_pictograms.get_width() / footer_pictograms.get_height() * footer_pictograms_height
        footer_pictograms = pygame.transform.smoothscale(footer_pictograms, (round(footer_pictograms_width), round(footer_pictograms_height))).convert_alpha()

    surf = pygame.Surface(px_size, pygame.SRCALPHA)

    pictograms_x = px_size[0] - footer_pictograms.get_width()
    surf.blit(footer_pictograms, (pictograms_x, px_size[1] // 2 - footer_pictograms.get_height() // 2))

    surf.blit(nyssefi_text, (pictograms_x - (nyssefi_text.get_width() // 5 * 0.7) - nyssefi_text.get_width(), px_size[1] // 2 - nyssefi_text.get_height() // 2))

    return surf