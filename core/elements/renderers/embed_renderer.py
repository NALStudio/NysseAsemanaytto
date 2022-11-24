import dataclasses
from types import EllipsisType
import pygame
from core import elements, render_info
import embeds

class EmbedRenderer(elements.ElementRenderer):
    def __init__(self) -> None:
        self.embed_data: render_info.CurrentEmbedData | None = None
        self.previous_frames: dict[embeds.Embed, tuple[pygame.Surface | None, elements.RenderFlags]] = {}
        self.last_embed_enable: float | None = None
        self.try_load_previous_frame: bool = False

    def setup(self) -> None:
        pass

    def update(self, context: elements.UpdateContext) -> bool:
        changes: bool = False

        with render_info.current_embed_data_lock: # TODO: Non blocking check
            if render_info.current_embed_data is not self.embed_data: # Handles None check
                self.embed_data = render_info.current_embed_data
                changes = True


        if self.embed_data is not None:
            first_frame: bool = False
            if self.last_embed_enable is None or self.last_embed_enable != self.embed_data.enabled_posix_timestamp:
                self.last_embed_enable = self.embed_data.enabled_posix_timestamp
                first_frame = True

            embed_on_duration: float = context.time.timestamp() - self.embed_data.enabled_posix_timestamp
            e_context = embeds.EmbedContext(first_frame, context)
            res: bool | EllipsisType = self.embed_data.embed.update(e_context, (embed_on_duration / self.embed_data.requested_duration))
            if isinstance(res, bool):
                changes = res
            else:
                self.try_load_previous_frame = True
                changes = True

        return changes

    def get_rect(self) -> pygame.Rect:
        embed_rect: pygame.Rect = elements.position_params.embed_rect
        if embed_rect.width < 0 or embed_rect.height < 0:
            raise RuntimeError("Embed rect too small!")
        return embed_rect

    def render(self, size: tuple[int, int], flags: elements.RenderFlags) -> pygame.Surface | None:
        if self.embed_data is None:
            return None

        if self.try_load_previous_frame:
            self.try_load_previous_frame = False
            if self.embed_data.embed in self.previous_frames:
                prev_surf, prev_flag = self.previous_frames[self.embed_data.embed]

                # Copy flag values
                for prev_flag_key, prev_flag_value in dataclasses.asdict(prev_flag).items():
                    setattr(flags, prev_flag_key, prev_flag_value)

                return prev_surf

        frame: pygame.Surface | None = self.embed_data.embed.render(size, flags)
        self.previous_frames[self.embed_data.embed] = (frame, flags) # replace makes a copy of the flags.
        return frame
