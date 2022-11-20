import threading
import time
from typing import NamedTuple
from core import logging, config, render_info, threadex
import embeds


class CurrentEmbedData(NamedTuple):
    embed: embeds.Embed
    requested_duration: float
    enabled_posix_timestamp: float

embed_index: int = -1
cycle_embed_timer: threading.Timer | None = None
cycle_running: bool = False

enabled_embeds: tuple[embeds.Embed, ...] | None = None

def _load_embeds() -> tuple[embeds.Embed, ...]:
    logging.debug(f"Loading embeds from config...", stack_info=False)
    all_embeds: list[embeds.Embed] = []

    for embed_launch_str in config.current.enabled_embeds:
        embed_launch: list[str] = embed_launch_str.split(" ")
        embed_name = embed_launch[0]
        embed_args = embed_launch[1:]

        prettyprint_args = ' '.join(embed_args)
        logging.debug(f"Loading new embed '{embed_name}' with arguments '{prettyprint_args}' into cache...", stack_info=False)

        valid_embeds: list[type[embeds.Embed]] = list(filter(lambda e: e.name() == embed_name, embeds.ALL_EMBEDS))
        assert len(valid_embeds) > 0, f"No embed named '{embed_name}' found!"
        assert len(valid_embeds) == 1, f"Multiple embeds named '{embed_name}' found!"

        all_embeds.append(valid_embeds[0](*embed_args))

    logging.debug(f"Embed loading complete.", stack_info=False)
    return tuple(all_embeds)

def _cycle_embed() -> None:
    global enabled_embeds, embed_index, cycle_embed_timer
    if enabled_embeds is None:
        enabled_embeds = _load_embeds()

    logging.debug("Switching embed...", stack_info=False)
    if len(enabled_embeds) < 1:
        logging.info("No embeds enabled! Cancelling embed cycling...", stack_info=False)
        cycle_embed_timer = None
        return

    new_embed: embeds.Embed | None = None
    while new_embed is None or new_embed.requested_duration() <= 0.0:
        embed_index = (embed_index + 1) % len(config.current.enabled_embeds)
        new_embed = enabled_embeds[embed_index]

    with render_info.current_embed_data_lock:
        # disable old
        if render_info.current_embed_data is not None:
            try:
                render_info.current_embed_data.embed.on_disable()
            except Exception as e:
                logging.dump_exception(e, cycle_embed_timer, "embedDisableFail")

        try:
            new_embed.on_enable()
        except Exception as e:
            logging.dump_exception(e, cycle_embed_timer, "embedEnableFail")
        render_info.current_embed_data = CurrentEmbedData(new_embed, new_embed.requested_duration(), time.time())

        cycle_embed_timer = threading.Timer(render_info.current_embed_data.requested_duration, _cycle_embed)
        cycle_embed_timer.daemon = False
        cycle_embed_timer.name = threadex.thread_names.name_with_identifier("EmbedCycleTimer")
        cycle_embed_timer.start()

def start_embed_cycling() -> None:
    global cycle_running
    if cycle_running:
        raise RuntimeError("Cannot start embed cycling. Embed cycling is already running.")

    cycle_running = True
    _cycle_embed()

def stop_embed_cycling() -> None:
    global cycle_running

    if cycle_embed_timer is not None:
        cycle_embed_timer.cancel()
    cycle_running = False
