from typing import Optional, Tuple
from core.config import Config
from core.colors import Colors
import core.renderers as renderers

import threading
import traceback
import os
import json

import digitransit.routing
import digitransit.enums

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import pygame.display
import pygame.image
import pygame.transform
import pygame.surface
import pygame.time
import pygame.font

class ConsoleColors:
    BLACK = "\u001b[30m"
    RED = "\u001b[31m"
    GREEN = "\u001b[32m"
    YELLOW = "\u001b[33m"
    BLUE = "\u001b[34m"
    MAGENTA = "\u001b[35m"
    CYAN = "\u001b[36m"
    WHITE = "\u001b[37m"
    RESET = "\u001b[0m"

print("Loading config...")
with open("config.json") as f:
    config: Config = json.loads(f.read(), object_hook=lambda d: Config(**d))
print("Config loaded.")

print("Starting stop info thread...")
def fetchInfo() -> Tuple[digitransit.routing.Stop, Optional[threading.Timer]]:
    global stopinfo, fetch_timer
    print(ConsoleColors.CYAN + "Fetching stop info..." + ConsoleColors.RESET)
    try:
        stopinfo = digitransit.routing.get_stop_info(config.endpoint, config.stopcode, config.departure_count)
    except Exception as e:
        print(ConsoleColors.RED + "An error occured while fetching stop info! Exception below:")
        print(ConsoleColors.YELLOW + f"{type(e).__name__}: {e}")
        print(traceback.format_exc() + ConsoleColors.RESET)
    if config.poll_rate > 0:
        fetch_timer = threading.Timer(config.poll_rate, fetchInfo)
        fetch_timer.start()
    return stopinfo, fetch_timer
stopinfo: digitransit.routing.Stop
fetch_timer: Optional[threading.Timer]
stopinfo, fetch_timer = fetchInfo()
print("Thread started.")

print("Creating window...")
pygame.init()
pygame.display.set_caption("Nysse Pysäkkinäyttö")
pygame.display.set_icon(pygame.image.load("resources/textures/icon.png"))
display_flags = pygame.RESIZABLE
if config.fullscreen:
    display_flags |= pygame.FULLSCREEN
display = pygame.display.set_mode(config.window_size, display_flags)
clock = pygame.time.Clock()
print("Window created.")
print(ConsoleColors.GREEN + "Finished!" + ConsoleColors.RESET)

debug: bool = False
debugFont: pygame.font.Font = pygame.font.Font("resources/fonts/Lato-Regular.ttf", 10)

running: bool = True
while running:
    display_size = display.get_size()
    content_width = display_size[0] - display_size[0] // 8
    content_offset = (display_size[0] - content_width) // 2
    content_spacing = round(content_offset * 0.3)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_F3:
                debug = not debug

    #region Background
    display.blit(renderers.background.renderBackground(display_size), (0, 0))
    #endregion

    #region Header
    header_rect = pygame.Rect(content_offset, content_offset, content_width, display_size[0] / 13)
    display.blit(renderers.header.renderHeader(header_rect.size, stopinfo.vehicleMode), header_rect.topleft)
    #endregion

    #region Stop Info
    stop_info_rect = pygame.Rect(content_offset, header_rect.bottom + content_spacing * 2, content_width, display_size[0] / 9)
    display.blit(renderers.stop_info.renderStopInfo(stop_info_rect.size, stopinfo), stop_info_rect.topleft)
    #endregion

    #region Stoptimes
    stoptime_height = stop_info_rect.height
    stoptime_y = 0
    stoptime_i = 0
    while stoptime_i < len(stopinfo.stoptimes) and ((stoptime_y < config.visible_count) if config.visible_count != None else True):
        stoptime = stopinfo.stoptimes[stoptime_i]
        if stoptime.headsign not in config.ignore_headsigns:
            stoptime_rect = pygame.Rect(content_offset, stop_info_rect.bottom + content_spacing + stoptime_y * (content_spacing / 2 + stoptime_height), content_width, stoptime_height)
            display.blit(renderers.stoptime.renderStoptime(stoptime_rect.size, stopinfo.stoptimes[stoptime_i]), stoptime_rect.topleft)

            stoptime_y += 1

        stoptime_i += 1
    #endregion

    #region Footer
    footer_rect = pygame.Rect(content_offset, -1, content_width, display_size[0] / 13)
    footer_rect.y = display_size[1] - content_offset - footer_rect.height
    display.blit(renderers.footer.renderFooter(footer_rect.size), footer_rect.topleft)
    #endregion

    #region Debug
    if debug:
        display.blit(debugFont.render(format(clock.get_fps(), ".3f"), True, Colors.WHITE), (0, 0))
    #endregion

    # NOTE: Assuming no animations are present which need accurate framerate timing and not clock.tick inaccuracies.
    # NOTE: Before pygame.display.flip, because input latency is not a worry. If we would take any inputs, we should put this after display flip.
    clock.tick(config.framerate)

    pygame.display.flip()
    display.fill(Colors.BLACK)

#region Quitting
if fetch_timer != None:
    fetch_timer.cancel()
#endregion