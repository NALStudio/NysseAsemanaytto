from typing import Optional
from core.config import Config
from core.colors import Colors
import core.renderers as renderers

import threading
import time
import os
import json

import digitransit.routing
import digitransit.enums

import nysse.pictogram

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import pygame.display
import pygame.image
import pygame.transform
import pygame.surface
import pygame.time
import pygame.font

print("Loading config...")
with open("config.json") as f:
    config: Config = json.loads(f.read(), object_hook=lambda d: Config(**d))
print("Config loaded.")

print("Starting stop info thread...")
stopinfo: digitransit.routing.Stop = digitransit.routing.get_stop_info(config.endpoint, config.stopcode)
def fetchInfo():
    global stopinfo
    stopinfo = digitransit.routing.get_stop_info(config.endpoint, config.stopcode)
if config.poll_rate > 0:
    threading.Timer(config.poll_rate, fetchInfo)
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
print("Finished!")

debug: bool = False
debugFont: pygame.font.Font = pygame.font.Font("resources/fonts/Lato-Regular.ttf", 10)

running: bool = True
while running:
    display_size = display.get_size()
    content_width = display_size[0] - display_size[0] // 8
    content_offset = (display_size[0] - content_width) // 2

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYUP:
            debug = not debug

    #region Header
    header_rect = pygame.Rect(content_offset, content_offset, content_width, round(display_size[1] / 23))
    display.blit(renderers.header.renderHeader(header_rect.size, stopinfo.vehicleMode), header_rect.topleft)
    #endregion

    #region Stop Info
    stop_info_rect = pygame.Rect(content_offset, header_rect.bottom + round(content_offset * 0.6), content_width, display_size[0] // 9)
    display.blit(renderers.stop_info.renderStopInfo(stop_info_rect.size, stopinfo), stop_info_rect.topleft)
    #endregion

    #region Debug
    if debug:
        display.blit(debugFont.render(format(clock.get_fps(), ".3f"), True, Colors.WHITE), (0, 0))
    #endregion

    pygame.display.flip()
    clock.tick_busy_loop(config.framerate)
    display.fill(Colors.BLACK)