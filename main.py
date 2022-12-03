import datetime
import os
import threading
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

from core import logging, config, render_info, debug, thread_exception_handler, renderer, elements, threadex

def main():
    init()

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
                elif event.key == pygame.K_F5:
                    renderer.force_rerender()
                elif event.key == pygame.K_F6:
                    if debug.render_enabled:
                        debug.render_enabled = False
                    elif debug.enabled:
                        debug.render_enabled = True
                elif event.key == pygame.K_F7:
                    if debug.rect_enabled:
                        debug.rect_enabled = False
                        renderer.force_rerender(size=renderer.get_size())
                    elif debug.enabled:
                        debug.rect_enabled = True
                        renderer.reset_debug_colors()
                        renderer.force_rerender(size=renderer.get_size())
            elif event.type == pygame.WINDOWSIZECHANGED:
                renderer.force_rerender(size=(event.x, event.y))
        #endregion

        renderer.update(context)
        renderer.render(context.time, config.current.framerate)

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
