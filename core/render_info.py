import random
import string
import time
from typing import NamedTuple
from core import config, logging
import embeds
import digitransit.routing
import threading

#region Stop info
def get_stop_gtfsId() -> str:
    return f"tampere:{config.current.stopcode:04d}"

stopinfo: digitransit.routing.Stop
fetch_stopinfo_timer: threading.Timer | None

def generate_thread_id(prefix: str, id_length: int = 4) -> str:
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=id_length))

def _stop_info_update_digitransit() -> None:
    global stopinfo, fetch_stopinfo_timer
    logging.info("Fetching stop info...", stack_info=False)
    try:
        stopinfo = digitransit.routing.get_stop_info(config.current.endpoint, get_stop_gtfsId(), config.current.departure_count, config.current.omit_non_pickups, config.current.omit_canceled)
    except Exception as e:
        logging.dump_exception(e, fetch_stopinfo_timer, "requestFail")
    if config.current.poll_rate > 0:
        fetch_stopinfo_timer = threading.Timer(config.current.poll_rate, _stop_info_update_digitransit)
        fetch_stopinfo_timer.name = generate_thread_id("StopInfoTimer_")
        fetch_stopinfo_timer.start()

def start_stop_info_fetch() -> None:
    _stop_info_update_digitransit()
    try:
        _ = stopinfo
    except NameError:
        raise RuntimeError("Initial stop info fetch failed!")
#endregion

#region Embed cycle
class CurrentEmbedData(NamedTuple):
    embed: embeds.Embed
    requested_duration: float
    enabled_posix_timestamp: float

current_embed_data: CurrentEmbedData | None = None
current_embed_data_lock: threading.Lock = threading.Lock()
embed_index: int = -1
cycle_embed_timer: threading.Timer | None = None

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
    global enabled_embeds, embed_index, current_embed_data, cycle_embed_timer
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

    with current_embed_data_lock:
        # disable old
        if current_embed_data is not None:
            try:
                current_embed_data.embed.on_disable()
            except Exception as e:
                logging.dump_exception(e, cycle_embed_timer, "embedDisableFail")

        try:
            new_embed.on_enable()
        except Exception as e:
            logging.dump_exception(e, cycle_embed_timer, "embedEnableFail")
        current_embed_data = CurrentEmbedData(new_embed, new_embed.requested_duration(), time.time())

        cycle_embed_timer = threading.Timer(current_embed_data.requested_duration, _cycle_embed)
        cycle_embed_timer.name = generate_thread_id("EmbedCycleTimer_")
        cycle_embed_timer.start()


def start_embed_cycling() -> None:
    _cycle_embed()
#endregion

def stop_timers() -> None:
    all_timers = (fetch_stopinfo_timer, cycle_embed_timer)

    for tm in all_timers:
        if tm is not None:
            tm.cancel()

