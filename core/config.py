from typing import List, Optional, Tuple


class Config:
    def __init__(self, stopcode: int, departure_count: int, poll_rate: int , endpoint: str, window_size: List[int], fullscreen: bool, framerate: int) -> None:
        self.stopcode: int = stopcode
        self.departure_count = departure_count
        self.poll_rate: int = poll_rate
        self.endpoint: str = endpoint
        self.window_size: Tuple[int, int] = (window_size[0], window_size[1])
        self.fullscreen: bool = fullscreen
        self.framerate: int = framerate