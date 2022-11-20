import pygame
from core import elements, render_info

class EmbedRenderer(elements.ElementRenderer):
    def __init__(self) -> None:
        self.embed_data: render_info.CurrentEmbedData | None = None

    def setup(self) -> None:
        pass

    def update(self, context: elements.UpdateContext) -> bool:
        changes: bool = False

        with render_info.current_embed_data_lock:
            assert render_info.current_embed_data is not None
            if render_info.current_embed_data is not self.embed_data:
                self.embed_data = render_info.current_embed_data
                changes = True

        assert self.embed_data is not None
        embed_on_duration: float = context.time.timestamp() - self.embed_data.enabled_posix_timestamp
        if self.embed_data.embed.update(context, (embed_on_duration / self.embed_data.requested_duration)):
            changes = True

        return changes

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        return params.embed_rect

    def render(self, size: tuple[int, int]) -> pygame.Surface | None:
        assert self.embed_data is not None
        return self.embed_data.embed.render(size)
