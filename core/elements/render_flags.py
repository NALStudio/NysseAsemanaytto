from dataclasses import dataclass


@dataclass
class RenderFlags:
    clear_background: bool = True
    rerender_colliding_elements: bool = False
