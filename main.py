import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

from core import logging
from core import colors
from core import renderers
from core import config
from core import render_info
from core import font_helper

logging.init()

logging.debug("Loading config...", stack_info=False)
config.init()
logging.debug("Config loaded.", stack_info=False)

logging.debug("Starting stop info thread...", stack_info=False)
render_info.start_stop_info_fetch()
logging.debug("Stop info thread started.", stack_info=False)

logging.debug("Starting embeds cycling thread...", stack_info=False)
render_info.start_embed_cycling()
logging.debug("Embeds cycling thread started.", stack_info=False)

logging.debug("Creating window...", stack_info=False)
pygame.init()
pygame.display.set_caption("Nysse Pysäkkinäyttö")
pygame.display.set_icon(pygame.image.load("resources/textures/icon.png"))
display_flags = pygame.RESIZABLE
if config.current.fullscreen:
    display_flags |= pygame.FULLSCREEN
display = pygame.display.set_mode(config.current.window_size, display_flags)
embed_surf: pygame.Surface | None = None
clock = pygame.time.Clock()
logging.debug("Window created.", stack_info=False)

pygame.mouse.set_visible(not config.current.hide_mouse)
logging.info(f"Mouse visibility: {pygame.mouse.get_visible()}", stack_info=False)

logging.info("Initialization Finished!", stack_info=False)

debug: bool = False
debugFont: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Regular.ttf", "debug")

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
    assert render_info.stopinfo.vehicleMode is not None
    display.blit(renderers.header.renderHeader(header_rect.size, render_info.stopinfo.vehicleMode), header_rect.topleft)
    #endregion

    #region Stop Info
    stop_info_rect = pygame.Rect(content_offset, header_rect.bottom + content_spacing * 2, content_width, display_size[0] / 9)
    display.blit(renderers.stop_info.renderStopInfo(stop_info_rect.size, render_info.stopinfo), stop_info_rect.topleft)
    #endregion

    #region Stoptimes
    stoptime_height = stop_info_rect.height
    stoptime_y_index = 0
    stoptime_i = 0
    last_stoptime_y = -1
    assert render_info.stopinfo.stoptimes is not None
    while stoptime_i < len(render_info.stopinfo.stoptimes) and ((stoptime_y_index < config.current.visible_count) if config.current.visible_count is not None else True):
        stoptime = render_info.stopinfo.stoptimes[stoptime_i]
        if stoptime.headsign not in config.current.ignore_headsigns:
            last_stoptime_y = stop_info_rect.bottom + content_spacing + stoptime_y_index * (content_spacing / 2 + stoptime_height)
            stoptime_rect = pygame.Rect(content_offset, last_stoptime_y, content_width, stoptime_height)
            display.blit(renderers.stoptime.renderStoptime(stoptime_rect.size, render_info.stopinfo.stoptimes[stoptime_i]), stoptime_rect.topleft)

            stoptime_y_index += 1

        stoptime_i += 1
    #endregion

    #region Footer
    footer_rect = pygame.Rect(content_offset, -1, content_width, display_size[0] / 13)
    footer_rect.y = display_size[1] - content_offset - footer_rect.height
    display.blit(renderers.footer.renderFooter(footer_rect.size), footer_rect.topleft)
    #endregion

    #region Embeds
    if render_info.embed is not None:
        embed_y = last_stoptime_y + stoptime_height + (2 * content_spacing)
        embed_height = footer_rect.y - embed_y - content_spacing
        embed_rect = pygame.Rect(0, embed_y, display_size[0], embed_height)
        if embed_rect.size[0] <= 0 or embed_rect.size[1] <= 0:
            logging.error("Window height too small for embed!")
        else:
            if embed_surf is None or embed_surf.get_size() != embed_rect.size:
                logging.debug("Creating embed surface...", stack_info=False)
                embed_surf = pygame.Surface(embed_rect.size)
            embed_surf.fill(colors.Colors.BLACK)  # Theoritcally could be in an else statement because new surfaces are always black, but whatever...
            render_info.embed.render(embed_surf)
            display.blit(embed_surf, embed_rect.topleft)
    #endregion

    #region Debug
    if debug:
        display.blit(debugFont.get_size(10).render(format(clock.get_fps(), ".3f"), True, colors.Colors.WHITE), (0, 0))
    #endregion

    # NOTE: Assuming no animations are present which need accurate framerate timing and not clock.tick inaccuracies.
    # NOTE: Before pygame.display.flip, because input latency is not a worry. If we would take any inputs, we should put this after display flip.
    clock.tick(config.current.framerate)

    pygame.display.flip()
    display.fill(colors.Colors.BLACK)

#region Quitting
render_info.stop_timers()
config.quit()
#endregion
