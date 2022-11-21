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
            if render_info.current_embed_data is not self.embed_data: # Handles None check
                self.embed_data = render_info.current_embed_data
                changes = True

        if self.embed_data is not None:
            embed_on_duration: float = context.time.timestamp() - self.embed_data.enabled_posix_timestamp
            if self.embed_data.embed.update(context, (embed_on_duration / self.embed_data.requested_duration)):
                changes = True

        return changes

    def get_rect(self, params: elements.ElementPositionParams) -> pygame.Rect:
        embed_rect: pygame.Rect = params.embed_rect
        if embed_rect.width < 0 or embed_rect.height < 0:
            raise RuntimeError("Embed rect too small!")
        return embed_rect

    def render(self, size: tuple[int, int], params: elements.ElementPositionParams, flags: elements.RenderFlags) -> pygame.Surface | None:
        if self.embed_data is None:
            return None

        return self.embed_data.embed.render(size, params, flags)
