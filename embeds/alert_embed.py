from __future__ import annotations
import threading

import embeds
import digitransit.routing
import time
from core import colors, config, font_helper, render_info, logging
import pygame

alert_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/OpenSans-Regular.ttf", "alert rendering")
page_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/OpenSans-Regular.ttf", "alert page number rendering")

class AlertEmbed(embeds.Embed):
    def __init__(self, *args: str):
        assert len(args) >= 3, "Invalid argument count!"

        self.poll_rate: int = int(args[0])
        assert isinstance(self.poll_rate, int), "First argument must be an integer defining alert poll rate! (Recommended: 300)"

        self.include_global: bool = bool(int(args[1]))
        assert isinstance(self.include_global, bool), "Second argument must be an integer 0 or 1 defining if global alerts should be included!"

        self.include_local: bool = bool(int(args[2]))
        assert isinstance(self.include_local, bool), "Third argument must be an integer 0 or 1 defining if alerts of routes which include displayed stop should be included!"

        self.remove_duplicates: bool = False
        if len(args) >= 4:
            self.remove_duplicates = bool(int(args[3]))
            assert isinstance(self.remove_duplicates, bool), "Fourth argument must be an integer 0 or 1 defining if duplicate alerts should be removed!"


        self.alerts: list[digitransit.routing.Alert] | None = None
        self.filtered_alerts: list[digitransit.routing.Alert] | None = None
        self.alert_index: int = 0
        self.last_update: float | None = None
        self.enable_time: float | None = None

    def on_enable(self):
        now_update = time.process_time()
        self.enable_time = now_update

        if self.last_update is None or now_update - self.last_update > self.poll_rate:
            logging.info(f"Loading new alert data...", stack_info=False)

            threading.Thread(target=self.load_and_filter_alerts, name="AlertsFetch").start()

            self.last_update = now_update
            # Not adding difference but rather setting the value
            # because accuracy is not really important
            # and it works nicer with the None check.

    def load_and_filter_alerts(self):
        alerts = digitransit.routing.get_alerts(config.current.endpoint, ("tampere",))

        filtered_alerts = [alert for alert in alerts if self._alert_meets_filter_requirements(alert)]

        # There seem to be duplicates during the 2022 Finnish Ice Hockey World Championship, but I don't think that normally happens...
        if self.remove_duplicates: # Remove duplicates by checking if the descriptions (the only visible part basically) are the same
            filtered_alerts = [alert for alert_index, alert in enumerate(filtered_alerts) if all(alert.alertDescriptionText != other.alertDescriptionText for other in filtered_alerts[:alert_index])]

        self.alerts = alerts # Values are set here due to threading
        self.filtered_alerts = filtered_alerts

    def on_disable(self):
        self.alert_index += 1
        self.enable_time = None # Probably not needed, but if something goes wrong this will force a crash instead of running half broken

    def _alert_meets_filter_requirements(self, alert: digitransit.routing.Alert) -> bool:
        def alert_is_global(alert: digitransit.routing.Alert) -> bool:
            return alert.route is None and alert.stop is None

        if not self.include_global and alert_is_global(alert): # Return false if global alerts are not included
            return False # Alert is global, False is returned
        if not self.include_local: # Return false if local alerts are not included
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

    def render(self, surface: pygame.Surface, content_spacing: int):
        BACKGROUND_COLOR = colors.Colors.WHITE
        BORDER_COLOR = colors.NysseColors.RATIKANPUNAINEN

        surface_size: tuple[int, int] = surface.get_size()
        border_radius = round(surface_size[1] / 15)
        border_width = round(content_spacing / 2)
        pygame.draw.rect(surface, BACKGROUND_COLOR, (0, 0, *surface_size), border_radius=border_radius)
        pygame.draw.rect(surface, BORDER_COLOR, (0, 0, *surface_size), border_width, border_radius=border_radius)

        filtered_alerts: list[digitransit.routing.Alert] | None = self.filtered_alerts # Value is set before if-check due to threading
        if filtered_alerts is None:
            return

        font = alert_font.get_size(round(surface_size[1] / 11))
        page_index_font = page_font.get_size(round(surface_size[1] / 20))

        # No alerts
        if len(filtered_alerts) < 1:
            no_alerts = font.render("Ei häiriöitä Nyssen toiminnassa.", True, (80, 80, 80))
            surface.blit(no_alerts, (surface_size[0] / 2 - no_alerts.get_width() / 2, surface_size[1] / 2 - no_alerts.get_height() / 2))
            return

        # DEBUG:
        # print("=" * 1000)
        # for alert in filtered_alerts:
        #     print("=" * 20)
        #     print(alert.alertHeaderText)
        #     print(f"{alert.route.shortName} | {alert.route.longName}" if alert.route is not None else None)
        #     if alert.stop is not None:
        #         print(f"{alert.stop.gtfsId}: {alert.stop.name}")
        # print("=" * 1000)

        self.alert_index %= len(filtered_alerts)
        alert = filtered_alerts[self.alert_index]

        text_rect = pygame.Rect(round(content_spacing * 1.5), round(content_spacing * 1.5), surface_size[0] - content_spacing * 3, surface_size[1] - content_spacing * 3)
        pages: list[font_helper.Page] = list(font_helper.pagination(font, alert.alertDescriptionText, text_rect.size))
        page_count = len(pages)

        time_per_page: float = self.duration() / page_count
        time_elapsed: float
        if self.enable_time is not None: # FUCK THREADING
            time_elapsed = time.process_time() - self.enable_time
        else:
            logging.warning("Alert embed enable time is None!")
            time_elapsed = time_per_page * page_count

        page_index = int(time_elapsed / time_per_page)
        if page_index >= page_count: # It is possible that the page index is greater than the number of pages at the end of the embed cycle.
            if page_index > page_count: # If the page index is 2 or more over the amount of pages, warn the user.
                logging.debug(f"Alert page index {page_index - (page_count - 1)} over the maximum page index.", stack_info=False)
            page_index = page_count - 1

        # Page index
        page_index_render = page_index_font.render(f"{page_index + 1}/{page_count}", True, colors.Colors.BLACK)
        surface.blit(page_index_render, (surface_size[0] - page_index_render.get_width() - content_spacing, content_spacing))

        # Text body
        page_render = font_helper.render_page(font, pages[page_index], True, colors.Colors.BLACK)
        surface.blit(page_render, text_rect.topleft)


    @staticmethod
    def name() -> str:
        return "alerts"

    @staticmethod
    def duration() -> float:
        return 30.0
