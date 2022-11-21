import pygame
from core import elements, font_helper
from core.colors import Colors

class FooterRenderer(elements.ElementRenderer):
    def update(self, context: elements.UpdateContext) -> bool:
        return False

    def setup(self) -> None:
        self.unscaled_footer_pictograms: pygame.Surface = pygame.image.load("resources/textures/elements/footer/footer_pictograms.png").convert_alpha()
        self.nyssefi_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lota-Grotesque-Bold.otf")

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        return params.footer_rect

    def render(self, size: tuple[int, int], params: elements.ElementPositionParams, flags: elements.RenderFlags) -> pygame.Surface | None:
        nyssefi_font_height: int = size[1]
        nyssefi_text = self.nyssefi_font.get_size(nyssefi_font_height).render("nysse.fi", True, Colors.WHITE)

        unscaled_pictograms: pygame.Surface = self.unscaled_footer_pictograms
        footer_pictograms_height: float = size[1] * 0.7
        footer_pictograms_width: float = unscaled_pictograms.get_width() / unscaled_pictograms.get_height() * footer_pictograms_height
        footer_pictograms = pygame.transform.smoothscale(unscaled_pictograms, (round(footer_pictograms_width), round(footer_pictograms_height)))

        surf = pygame.Surface(size, pygame.SRCALPHA)

        pictograms_x = size[0] - footer_pictograms.get_width()
        surf.blit(footer_pictograms, (pictograms_x, size[1] // 2 - footer_pictograms.get_height() // 2))

        surf.blit(nyssefi_text, (pictograms_x - (nyssefi_text.get_width() // 5 * 0.7) - nyssefi_text.get_width(), size[1] // 2 - nyssefi_text.get_height() // 2))

        return surf
