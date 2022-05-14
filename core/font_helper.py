import pygame

class SizedFont:
    def __init__(self, path: str, purpose: str | None = None) -> None:
        self._path: str = path
        self._loaded_size: int | None = None
        self._font: pygame.font.Font | None = None

        self._purpose: str | None = purpose

    def get_size(self, size: int) -> pygame.font.Font:
        if self._font is None or size != self._loaded_size:
            if self._purpose is not None:
                print(f"Loading new font for {self._purpose}...")

            self._loaded_size = size
            self._font = pygame.font.Font(self._path, size)

        return self._font
