import datetime
import os
import threading
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import psutil

from core import logging, colors, renderers, config, render_info, font_helper, debug, clock, thread_exception_handler

def main():
    #region Initialization
    logging.init()

    threading.excepthook = thread_exception_handler.thread_excepthook

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
    pygame.display.set_caption("Nysse Asemanäyttö")
    pygame.display.set_icon(pygame.image.load("resources/textures/icon.png"))
    display_flags = pygame.RESIZABLE
    if config.current.fullscreen:
        display_flags |= pygame.FULLSCREEN
    display = pygame.display.set_mode(config.current.window_size, display_flags)
    embed_surf: pygame.Surface | None = None
    logging.debug("Window created.", stack_info=False)

    logging.debug("Initializing variables...", stack_info=False)
    debugFont: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/Lato-Regular.ttf", "debug")
    logging.debug("Variables initialized.", stack_info=False)

    pygame.mouse.set_visible(not config.current.hide_mouse)
    logging.info(f"Mouse visibility: {pygame.mouse.get_visible()}", stack_info=False)

    logging.info("Initialization Finished!", stack_info=False)
    #endregion

    running: bool = True
    while running:
        #region Render params
        display_size: tuple[int, int] = display.get_size()
        content_width: int = display_size[0] - (display_size[0] // 8)
        content_offset: int = (display_size[0] - content_width) // 2
        content_spacing: int = round(content_offset * 0.3)
        current_time: datetime.datetime = datetime.datetime.now()
        #endregion

        #region Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_F2:
                    debug.process_enabled = not debug.process_enabled
                elif event.key == pygame.K_F3:
                    debug.enabled = not debug.enabled
                elif event.key == pygame.K_F4:
                    if debug.profiler.is_enabled():
                        debug.profiler.disable()
                    elif debug.enabled: # Checking this so someone doesn't accidentally turn it on while playing
                        debug.profiler.enable()
        #endregion

        #region Header
        header_rect: pygame.Rect = pygame.Rect(content_offset, content_offset, content_width, display_size[0] / 13)
        assert render_info.stopinfo.vehicleMode is not None
        display.blit(renderers.header.render_header(header_rect.size, render_info.stopinfo.vehicleMode, current_time.time()), header_rect.topleft)
        #endregion

        #region Stop Info
        stop_info_rect: pygame.Rect = pygame.Rect(content_offset, header_rect.bottom + content_spacing * 2, content_width, display_size[0] / 9)
        display.blit(renderers.stop_info.render_stopinfo(stop_info_rect.size, render_info.stopinfo), stop_info_rect.topleft)
        #endregion

        #region Stoptimes
        stoptime_height: int = stop_info_rect.height
        last_stoptime_y: float | None = None
        assert render_info.stopinfo.stoptimes is not None

        for stoptime_i in range(len(render_info.stopinfo.stoptimes)):
            last_stoptime_y = stop_info_rect.bottom + content_spacing + stoptime_i * (content_spacing / 2 + stoptime_height)
            stoptime_rect = pygame.Rect(content_offset, last_stoptime_y, content_width, stoptime_height)
            display.blit(renderers.stoptime.render_stoptime(stoptime_rect.size, render_info.stopinfo.stoptimes[stoptime_i], current_time), stoptime_rect.topleft)
        #endregion

        #region Footer
        footer_rect: pygame.Rect = pygame.Rect(content_offset, -1, content_width, display_size[0] / 13)
        footer_rect.y = display_size[1] - content_offset - footer_rect.height
        display.blit(renderers.footer.render_footer(footer_rect.size), footer_rect.topleft)
        #endregion

        #region Embeds
        assert last_stoptime_y is not None
        embed_y: int = round(last_stoptime_y) + stoptime_height + (2 * content_spacing)
        embed_height: int = footer_rect.y - embed_y - content_spacing
        embed_rect: pygame.Rect = pygame.Rect(0, embed_y, display_size[0], embed_height)
        if embed_surf is None or embed_surf.get_size() != embed_rect.size:
            logging.debug("Creating embed surface...", stack_info=False)
            embed_surf = pygame.Surface(embed_rect.size, pygame.SRCALPHA)
        embed_surf.fill(0)  # Theoritcally could be in an else statement because SRCALPHA will make it transparent by default

        with render_info.current_embed_data_lock:
            embed_data: render_info.CurrentEmbedData | None = render_info.current_embed_data
            if embed_data is not None:
                if embed_rect.size[0] <= 0 or embed_rect.size[1] <= 0:
                    logging.error("Window height too small for embed!")
                else:
                    embed_on_duration: float = current_time.timestamp() - embed_data.enabled_posix_timestamp
                    embed_data.embed.render(embed_surf, content_spacing, current_time, (embed_on_duration / embed_data.requested_duration))
                    display.blit(embed_surf, embed_rect.topleft)
        #endregion

        #region Debug
        if debug.enabled:
            memory_usage_msg: str = "disabled"
            thread_count_msg: str = "disabled"

            thread_fields: list[tuple[str, object]] = []
            if debug.process_enabled:
                process = psutil.Process(os.getpid())
                memory_full_info = process.memory_full_info()
                memory_usage_msg = f"{memory_full_info.uss / 1_048_576:.1f} MB ({(memory_full_info.rss / psutil.virtual_memory().available) * 100:.1f} %)"

                for thread in threading.enumerate():
                    thread_fields.append((f"    {thread.name}", thread.ident))
                thread_count_msg = str(len(thread_fields))

            fields = debug.get_fields(
                ("Frametime", f"{clock.get_frametime(3):.2f} ms"),
                ("Raw Frametime", f"{clock.get_raw_frametime(3):.2f} ms"),
                ("Memory Usage", memory_usage_msg),
                (f"Threads", thread_count_msg),
                *thread_fields
            )

            font = debugFont.get_size(14)
            renders = [
                font.render(f"{name}: {value}", True, colors.Colors.WHITE)
                for name, value in fields
            ]

            width = max(renders, key=lambda render: render.get_width()).get_width()
            height = len(renders) * font.get_linesize()
            debug_background: pygame.Surface = pygame.Surface((width, height))
            debug_background.set_alpha(128)

            display.blit(debug_background, (0, 0))
            for i, render in enumerate(renders):
                display.blit(render, (0, i * font.get_linesize()))
        #endregion

        #region Display update
        pygame.display.flip()

        # NOTE: Assuming no animations are present which need accurate framerate timing and not clock.tick inaccuracies.
        clock.tick(config.current.framerate)

        background: pygame.Surface = renderers.background.render_background(display_size)
        assert background.get_size() == display_size
        display.blit(background, (0, 0))
        #endregion

    quit()

def quit():
    render_info.stop_timers()
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
