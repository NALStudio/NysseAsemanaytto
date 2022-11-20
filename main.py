import datetime
import os
import threading
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import psutil

from core import logging, colors, config, render_info, font_helper, debug, thread_exception_handler, renderer, elements, threadex
import copy
from digitransit.routing import Stoptime

def main():
    init()

    embed_surf: pygame.Surface | None = None
    debugFont: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Regular.ttf", "debug")

    temp_element_position_params: elements.ElementPositionParams = elements.ElementPositionParams()

    running: bool = True
    while running:
        context: elements.UpdateContext = elements.UpdateContext(datetime.datetime.now(), render_info.stopinfo)

        #region Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_F2:
                    debug.process_enabled = not debug.process_enabled
                elif event.key == pygame.K_F3:
                    debug.enabled = not debug.enabled
                elif event.key == pygame.K_F4:
                    if debug.profiler.is_enabled():
                        debug.profiler.disable()
                    elif debug.enabled: # Checking this so someone doesn't accidentally turn it on while playing
                        debug.profiler.enable()
                elif event.key == pygame.K_F6:
                    if debug.render_enabled:
                        debug.render_enabled = False
                    elif debug.enabled:
                        debug.render_enabled = True
                elif event.key == pygame.K_F7:
                    if debug.rect_enabled:
                        debug.rect_enabled = False
                        renderer.force_render()
                    elif debug.enabled:
                        debug.rect_enabled = True
                        renderer.reset_debug_colors()
                        renderer.force_render()
            elif event.type == pygame.WINDOWSIZECHANGED:
                renderer.force_render()
        #endregion

        #region Header
        # assert render_info.stopinfo.vehicleMode is not None
        # renderer.temp_blit(__renderers.header.render_header(element_position_params.header_rect.size, render_info.stopinfo.vehicleMode, current_time.time()), element_position_params.header_rect.topleft)
        #endregion

        #region Stop Info
        # renderer.temp_blit(__renderers.stop_info.render_stopinfo(element_position_params.stop_info_rect.size, render_info.stopinfo), element_position_params.stop_info_rect.topleft)
        #endregion

        #region Stoptimes
        # assert render_info.stopinfo.stoptimes is not None
        #
        # for stoptime_i in range(len(render_info.stopinfo.stoptimes)):
        #     stoptime_rect = element_position_params.get_stoptime_rect(stoptime_i)
        #     renderer.temp_blit(__renderers.stoptime.render_stoptime(stoptime_rect.size, render_info.stopinfo.stoptimes[stoptime_i], context.time), stoptime_rect.topleft)
        #endregion

        #region Footer
        # renderer.temp_blit(__renderers.footer.render_footer(element_position_params.footer_rect.size), element_position_params.footer_rect.topleft)
        #endregion

        #region Embeds
        # if embed_surf is None or embed_surf.get_size() != temp_element_position_params.embed_rect.size:
        #     logging.debug("Creating embed surface...", stack_info=False)
        #     embed_surf = pygame.Surface(temp_element_position_params.embed_rect.size, pygame.SRCALPHA)
        # embed_surf.fill(0)  # Theoritcally could be in an else statement because SRCALPHA will make it transparent by default
        #
        # with render_info.current_embed_data_lock:
        #     embed_data: render_info.CurrentEmbedData | None = render_info.current_embed_data
        #     if embed_data is not None:
        #         if temp_element_position_params.embed_rect.size[0] <= 0 or temp_element_position_params.embed_rect.size[1] <= 0:
        #             logging.error("Window height too small for embed!")
        #         else:
        #             embed_on_duration: float = context.time.timestamp() - embed_data.enabled_posix_timestamp
        #             embed_data.embed.render(embed_surf, temp_element_position_params.content_spacing, context.time, (embed_on_duration / embed_data.requested_duration))
        #             renderer.temp_blit(embed_surf, temp_element_position_params.embed_rect.topleft)
        #endregion

        #region Debug
        # if debug.enabled:
        #     memory_usage_msg: str = "disabled"
        #     thread_count_msg: str = "disabled"
        #
        #     thread_fields: list[tuple[str, object]] = []
        #     if debug.process_enabled:
        #         process = psutil.Process(os.getpid())
        #         memory_full_info = process.memory_full_info()
        #         memory_usage_msg = f"{memory_full_info.uss / 1_048_576:.1f} MB ({(memory_full_info.rss / psutil.virtual_memory().available) * 100:.1f} %)"
        #
        #         for thread in threading.enumerate():
        #             thread_fields.append((f"    {thread.name}", thread.ident))
        #         thread_count_msg = str(len(thread_fields))
        #
        #     fields = debug.get_fields(
        #         ("Frametime", f"{renderer.get_frametime(3):.2f} ms"),
        #         ("Raw Frametime", f"{renderer.get_raw_frametime(3):.2f} ms"),
        #         ("Memory Usage", memory_usage_msg),
        #         (f"Threads", thread_count_msg),
        #         *thread_fields
        #     )
        #
        #     font = debugFont.get_size(14)
        #     renders = [
        #         font.render(f"{name}: {value}", True, colors.Colors.WHITE)
        #         for name, value in fields
        #     ]
        #
        #     width = max(renders, key=lambda render: render.get_width()).get_width()
        #     height = len(renders) * font.get_linesize()
        #     debug_background: pygame.Surface = pygame.Surface((width, height))
        #     debug_background.set_alpha(128)
        #
        #     renderer.temp_blit(debug_background, (0, 0))
        #     for i, render in enumerate(renders):
        #         renderer.temp_blit(render, (0, i * font.get_linesize()))
        #endregion

        renderer.update(context)
        renderer.render(context.time)

    quit()

def initialize_renderers():
    renderer.add_renderer(elements.HeaderIconsRenderer())
    renderer.add_renderer(elements.HeaderNysseRenderer())
    renderer.add_renderer(elements.HeaderTimeRenderer())

    renderer.add_renderer(elements.StopInfoRenderer())
    renderer.add_renderer(elements.FooterRenderer())
    renderer.add_renderer(elements.EmbedRenderer())

    renderer.add_renderer(elements.DebugRenderer())

    for i in range(config.current.departure_count):
        shortname = elements.StoptimeShortnameRenderer(i)
        time = elements.StoptimeTimeRenderer(i)
        headsign = elements.StoptimeHeadsignRenderer(i, shortname, time)

        renderer.add_renderer(shortname)
        renderer.add_renderer(headsign)
        renderer.add_renderer(time)

def init():
    #region Initialization
    logging.init()

    threading.excepthook = thread_exception_handler.thread_excepthook

    logging.debug("Loading config...", stack_info=False)
    config.init()

    logging.debug("Starting timers...", stack_info=False)
    start_timers()

    logging.debug("Initializing renderers...", stack_info=False)
    initialize_renderers()

    logging.debug("Creating window...", stack_info=False)
    pygame.init()
    renderer_flags: int = pygame.RESIZABLE
    if config.current.fullscreen:
        renderer_flags |= pygame.FULLSCREEN
    renderer.init(config.current.window_size, renderer_flags)

    pygame.mouse.set_visible(not config.current.hide_mouse)
    logging.info(f"Mouse visibility: {pygame.mouse.get_visible()}", stack_info=False)

    logging.info("Initialization Finished!", stack_info=False)
    #endregion

timers: list[threadex.RepeatingTimer] = []
def start_timers():
    stopinfo = threadex.RepeatingTimer("StopInfoTimer", config.current.poll_rate, render_info.update_stopinfo)
    timers.append(stopinfo)
    stopinfo.start_synchronous()

    render_info.start_embed_cycling()

def quit():
    for t in timers:
        t.cancel()

    render_info.stop_embed_cycling()

    config.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.dump_exception(e, threading.current_thread())

        try:
            quit()
        except Exception as e:
            logging.dump_exception(e, note="crashcleanup")
