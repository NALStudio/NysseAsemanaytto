from __future__ import annotations
import datetime
import threading
import time

import embeds
import digitransit.routing
from core import colors, config, elements, font_helper, render_info, logging, debug
from nalpy import math
import pygame

alert_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/OpenSans-Regular.ttf", "alert rendering")
page_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/OpenSans-Regular.ttf", "alert page number rendering")

# class AlertEmbed(embeds.Embed):
#     def __init__(self, *args: str):
#         assert len(args) >= 5, "Invalid argument count!"
#
#         self.poll_rate: int = int(args[0])
#         assert isinstance(self.poll_rate, int), "First argument must be an integer defining alert poll rate seconds! (Recommended: 300)"
#
#         self.include_global: bool = bool(int(args[1]))
#         assert isinstance(self.include_global, bool), "Second argument must be an integer 0 or 1 defining if global alerts should be included!"
#
#         self.include_local: bool = bool(int(args[2]))
#         assert isinstance(self.include_local, bool), "Third argument must be an integer 0 or 1 defining if alerts of routes which include displayed stop should be included!"
#
#         self.remove_duplicates: bool = bool(int(args[3]))
#         assert isinstance(self.remove_duplicates, bool), "Fourth argument must be an integer 0 or 1 defining if duplicate alerts should be removed!"
#
#         self.display_if_no_alerts: bool = bool(int(args[4]))
#         assert isinstance(self.display_if_no_alerts, bool), "Fifth argument must be an integer 0 or 1 defining if alert window should be displayed if there are no alerts active!"
#
#         self.alerts: list[digitransit.routing.Alert] | None = None
#         self.filtered_alerts: list[digitransit.routing.Alert] | None = None
#         self._alert_index: int = 0
#         self.last_update: float | None = None
#
#         self.no_alerts_render_cache: tuple[pygame.font.Font, pygame.Surface, tuple[int, int]] | None = None
#
#     def on_enable(self):
#         now_update: float = time.time()
#         if self.last_update is None or (now_update - self.last_update) > self.poll_rate:
#             logging.info(f"Loading new alert data...", stack_info=False)
#
#             threading.Thread(target=self.load_and_filter_alerts, name="AlertsFetch", daemon=False).start()
#
#             self.last_update = now_update
#             # Not adding difference but rather setting the value
#             # because accuracy is not really important
#             # and it works nicer with the None check.
#
#     def load_and_filter_alerts(self):
#         alerts = digitransit.routing.get_alerts(config.current.endpoint, ("tampere",))
#
#         filtered_alerts = [alert for alert in alerts if self._alert_meets_filter_requirements(alert)]
#
#         # There seem to be duplicates during the 2022 Finnish Ice Hockey World Championship, but I don't think that normally happens...
#         if self.remove_duplicates: # Remove duplicates by checking if the descriptions (the only visible part basically) are the same
#             filtered_alerts = [alert for alert_index, alert in enumerate(filtered_alerts) if all(alert.alertDescriptionText != other.alertDescriptionText for other in filtered_alerts[:alert_index])]
#
#         self.alerts = alerts # Values are set here due to threading
#         self.filtered_alerts = filtered_alerts
#
#     def on_disable(self):
#         filtered_alerts: list[digitransit.routing.Alert] | None = self.filtered_alerts
#
#         alert: digitransit.routing.Alert | None = None
#         if filtered_alerts is not None and len(filtered_alerts) > 0:
#             self._alert_index += 1
#             self._alert_index %= len(filtered_alerts)
#             alert = filtered_alerts[self._alert_index]
#
#         self.alert: digitransit.routing.Alert | None = alert
#         self.alert_pages: list[font_helper.Page] | None = None
#         self.page_index: int | None = None
#
#     def _alert_meets_filter_requirements(self, alert: digitransit.routing.Alert) -> bool:
#         def alert_is_global(alert: digitransit.routing.Alert) -> bool:
#             return alert.route is None and alert.stop is None
#
#         if not self.include_global and alert_is_global(alert): # Return false if global alerts are not included
#             return False # Alert is global, False is returned
#         if not self.include_local: # Return false if local alerts are not included
#             if not alert_is_global(alert):
#                 return False # Alert is local, False is returned
#         else: # Local alerts are included
#             if alert_is_global(alert): # Global alert handling is handled earlier. If it is global, it must be valid.
#                 return True # Alert is global, True is returned
#
#             rendered_stop_gtfsId = render_info.get_stop_gtfsId()
#
#             # Alert is local
#             if alert.stop is not None and alert.stop.gtfsId != rendered_stop_gtfsId: # Return false if the alert has defined a stop that is not the same as the displayed stop
#                 return False # Alert is local and it does not apply to the displayed stop, False is returned
#
#             assert alert.route is not None # This check is handled by global check
#             if alert.route.stops is None: # No stops defined for the route. Return false with error.
#                 logging.error("No stops defined for alert's route!")
#                 return False # Insufficient route info, False is returned
#
#             if all(stop.gtfsId != rendered_stop_gtfsId for stop in alert.route.stops): # Return false if the alert's route does not include the displayed stop
#                 return False # Alert is local and it does not apply to the displayed stop, False is returned
#
#         return True # Passed all checks
#
#     def update(self, context: elements.UpdateContext, progress: float) -> bool:
#         changes: bool = False
#
#         if self.alert_pages is None:
#             changes = True
#             self.page_index = 0
#         else:
#             page_count: int = len(self.alert_pages)
#             page_index = int(math.lerp(0, page_count + 1, progress)) # get page index by flooring interpolated value
#             if page_index >= page_count: # It is possible that the page index is greater than the number of pages at the end of the embed cycle.
#                 if page_index > page_count: # If the page index is 2 or more over the amount of pages, warn the user.
#                     logging.warning(f"Alert page index {page_index - (page_count - 1)} over the maximum page index.", stack_info=False)
#                 page_index = page_count - 1
#
#             if page_index != self.page_index:
#                 self.page_index = page_index
#                 changes = True
#
#         return changes
#
#     def render(self, size: tuple[int, int], params: elements.ElementPositionParams) -> pygame.Surface | None:
#         surf = pygame.Surface(size)
#
#         BACKGROUND_COLOR = colors.Colors.WHITE
#         BORDER_COLOR = colors.NysseColors.RATIKANPUNAINEN
#
#         content_spacing: int = params.content_spacing
#
#         border_radius = round(size[1] / 15)
#         border_width = round(content_spacing / 2)
#         border_rect: tuple[int, int, int, int] = (0, 0, *size)
#         pygame.draw.rect(surf, BACKGROUND_COLOR, border_rect, border_radius=border_radius)
#         pygame.draw.rect(surf, BORDER_COLOR, border_rect, border_width, border_radius=border_radius)
#
#         font = alert_font.get_size(round(size[1] / 11))
#         page_index_font = page_font.get_size(round(size[1] / 20))
#
#         # No alerts
#         if self.alert is None:
#             if self.no_alerts_render_cache is None or self.no_alerts_render_cache[0] != font:
#                 logging.debug("Rendering new no alerts message...", stack_info=False)
#                 no_alerts_render = font.render("Ei häiriöitä Nyssen toiminnassa.", True, (80, 80, 80))
#                 self.no_alerts_render_cache = (font, no_alerts_render, no_alerts_render.get_size())
#
#             surf.blit(self.no_alerts_render_cache[1], (size[0] / 2 - self.no_alerts_render_cache[2][0] / 2, size[1] / 2 - self.no_alerts_render_cache[2][1] / 2))
#             return
#
#         text_rect = pygame.Rect(round(content_spacing * 1.5), round(content_spacing * 1.5), size[0] - content_spacing * 3, size[1] - content_spacing * 3)
#         pages: list[font_helper.Page] = list(font_helper.pagination(font, self.alert.alertDescriptionText, text_rect.size))
#         page_count = len(pages)
#
#         assert self.page_index is not None
#
#         # Page index
#         if page_count > 1:
#             page_index_render = page_index_font.render(f"{self.page_index + 1}/{page_count}", True, colors.Colors.BLACK)
#             surf.blit(page_index_render, (size[0] - page_index_render.get_width() - content_spacing, content_spacing))
#
#         # Text body
#         if 0 <= self.page_index < len(pages):
#             page_render = font_helper.render_page(font, pages[self.page_index], True, colors.Colors.BLACK, BACKGROUND_COLOR)
#             surf.blit(page_render, text_rect.topleft)
#         else:
#             logging.error(f"Invalid page index: {self.page_index}")
#
#
#     @staticmethod
#     def name() -> str:
#         return "alerts"
#
#     def requested_duration(self) -> float:
#         return -1.0 if not self.display_if_no_alerts and self.alert is None else 15.0
#

class AlertEmbed(embeds.Embed):
    def __init__(self, *args: str):
        assert len(args) >= 5, "Invalid argument count!"

        self.poll_rate: int = int(args[0])
        assert isinstance(self.poll_rate, int), "First argument must be an integer defining alert poll rate seconds! (Recommended: 300)"

        self.include_global: bool = bool(int(args[1]))
        assert isinstance(self.include_global, bool), "Second argument must be an integer 0 or 1 defining if global alerts should be included!"

        self.include_local: bool = bool(int(args[2]))
        assert isinstance(self.include_local, bool), "Third argument must be an integer 0 or 1 defining if alerts of routes which include displayed stop should be included!"

        self.remove_duplicates: bool = bool(int(args[3]))
        assert isinstance(self.remove_duplicates, bool), "Fourth argument must be an integer 0 or 1 defining if duplicate alerts should be removed!"

        self.display_if_no_alerts: bool = bool(int(args[4]))
        assert isinstance(self.display_if_no_alerts, bool), "Fifth argument must be an integer 0 or 1 defining if alert window should be displayed if there are no alerts active!"

        self._alerts: list[digitransit.routing.Alert] | None = None
        self._filtered_alerts: list[digitransit.routing.Alert] | None = None
        self._alert_index: int = 0

    def load_and_filter_alerts(self):
        alerts = digitransit.routing.get_alerts(config.current.endpoint, ("tampere",))

        filtered_alerts = [alert for alert in alerts if _alert_meets_filter_requirements(alert, self.include_global, self.include_local)]

        # There seem to be duplicates during the 2022 Finnish Ice Hockey World Championship, but I don't think that normally happens...
        if self.remove_duplicates: # Remove duplicates by checking if the descriptions (the only visible part basically) are the same
            filtered_alerts = [alert for alert_index, alert in enumerate(filtered_alerts) if all(alert.alertDescriptionText != other.alertDescriptionText for other in filtered_alerts[:alert_index])]

        self._alerts = alerts # Values are set here due to threading
        self._filtered_alerts = filtered_alerts

    def on_enable(self):
        self.alert: digitransit.routing.Alert | None = None
        filtered_alerts: list[digitransit.routing.Alert] | None = self._filtered_alerts
        assert filtered_alerts is not None
        if len(filtered_alerts) > 0:
            self.alert = filtered_alerts[self._alert_index % len(filtered_alerts)]

    def on_disable(self):
        self._alert_index += 1
        if self._alerts is not None:
            self._alert_index %= (2 * len(self._alerts)) # Calculated so that alert_index doesn't cause a memory leak

    def update(self, context: elements.UpdateContext, progress: float) -> bool:
        debug.add_custom_field("Alert Index", self._alert_index)

    def render(self, size: tuple[int, int], params: elements.ElementPositionParams) -> pygame.Surface | None:
        pass


def _alert_meets_filter_requirements(alert: digitransit.routing.Alert, include_global: bool, include_local: bool) -> bool:
    def alert_is_global(alert: digitransit.routing.Alert) -> bool:
        return alert.route is None and alert.stop is None

    if not include_global and alert_is_global(alert): # Return false if global alerts are not included
        return False # Alert is global, False is returned
    if not include_local: # Return false if local alerts are not included
        if not alert_is_global(alert):
            return False # Alert is local, False is returned
    else: # Local alerts are included
        if alert_is_global(alert): # Global alert handling is handled earlier. If it is global, it must be valid.
            return True # Alert is global, True is returned

        rendered_stop_gtfsId = render_info.get_stop_gtfsId()

        # Alert is local
        if alert.stop is not None and alert.stop.gtfsId != rendered_stop_gtfsId: # Return false if the alert has defined a stop that is not the same as the displayed stop
            return False # Alert is local and it does not apply to the displayed stop, False is returned

        assert alert.route is not None # This check is handled by global check
        if alert.route.stops is None: # No stops defined for the route. Return false with error.
            logging.error("No stops defined for alert's route!")
            return False # Insufficient route info, False is returned
        if all(stop.gtfsId != rendered_stop_gtfsId for stop in alert.route.stops): # Return false if the alert's route does not include the displayed stop
            return False # Alert is local and it does not apply to the displayed stop, False is returned

    return True # Passed all checks
