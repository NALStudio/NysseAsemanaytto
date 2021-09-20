from pygame.constants import RESIZABLE
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

print("Loading config...")
with open("config.json") as f:
    config: Config = json.loads(f.read(), object_hook=lambda d: Config(**d))
print("Config loaded.")

print("Starting stop info thread...")
stopinfo: digitransit.routing.Stop = digitransit.routing.get_stop_info(config.endpoint, config.stopcode)
def fetchInfo():
    global stopinfo
    stopinfo = digitransit.routing.get_stop_info(config.endpoint, config.stopcode)
threading.Timer(config.poll_rate, fetchInfo)
while stopinfo == None:
    time.sleep(1.0)
print("Thread started.")

print("Creating window...")
pygame.init()
pygame.display.set_caption("Nysse Pysäkkinäyttö")
pygame.display.set_icon(pygame.image.load("resources/textures/icon.png"))
display_flags = RESIZABLE
if config.fullscreen:
    display_flags |= pygame.FULLSCREEN
display = pygame.display.set_mode(config.window_size, display_flags)
print("Finished!")

running: bool = True
while running:
    display_size = display.get_size()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    #region Stop Info
    stop_info_size = (display_size[0] - display_size[0] // 7, display_size[0] // 7)
    display.blit(renderers.stop_info.renderStopInfo(stop_info_size, stopinfo), (display_size[0] // 2 - stop_info_size[0] // 2, display_size[1] / 5))
    #endregion

    pygame.display.flip()
    display.fill(Colors.BLACK)