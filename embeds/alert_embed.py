from __future__ import annotations

import embeds
import digitransit.routing
import time
from core import colors, config
import pygame

class AlertEmbed(embeds.Embed):
    def __init__(self, *args: str):
        assert len(args) == 3, "Invalid argument count!"

        self.poll_rate: int = int(args[0])
        assert isinstance(self.poll_rate, int), "First argument must be an integer defining alert poll rate! (Recommended: 300)"

        self.include_global: bool = bool(args[1])
        assert isinstance(self.include_global, bool), "Second argument must be a boolean defining if global alerts should be included!"

        self.shortname_whitelist: list[str] | None = args[2].split(",") if args[2] != "..." else None
        assert self.shortname_whitelist is None or isinstance(self.shortname_whitelist, list), "Third argument must be a list of strings defining alert shortnames to include! (If '...', all alerts are included)"


        self.alerts: list[digitransit.routing.Alert] | None = None
        self.last_update: float | None = None

    def on_enable(self):
        now_update = time.process_time()
        if self.last_update is None or now_update - self.last_update > self.poll_rate:
            print(f"Loading new alert data...")

            self.alerts = digitransit.routing.get_alerts(config.current.endpoint)

            self.last_update = now_update
            # Not adding difference but rather setting the value
            # because accuracy is not really important
            # and it works nicer with the None check.

    def render(self, surface: pygame.Surface):
        BACKGROUND_COLOR = colors.Colors.WHITE

        surface.fill(BACKGROUND_COLOR)

        if self.alerts is None:
            return

        # render it here pls

    @staticmethod
    def name() -> str:
        return "alerts"

    @staticmethod
    def duration() -> float:
        return 30.0
