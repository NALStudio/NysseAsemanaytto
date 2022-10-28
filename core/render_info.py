import random
import string
from core import colors
from core import config
from core import logging
import embeds
import digitransit.routing
import traceback
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
        stopinfo = digitransit.routing.get_stop_info(config.current.endpoint, get_stop_gtfsId(), config.current.departure_count)
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
embed: embeds.Embed | None = None
embed_index: int = -1
cycle_embed_timer: threading.Timer | None

embed_cache: dict[int, embeds.Embed] = {}

def _cycle_embed() -> None:
    global embed, embed_index, cycle_embed_timer
    logging.debug("Switching embed...", stack_info=False)
    if len(config.current.enabled_embeds) < 1:
        logging.info("No embeds enabled! Cancelling embed cycling...", stack_info=False)
        cycle_embed_timer = None
        return

    embed_index = (embed_index + 1) % len(config.current.enabled_embeds)

    if embed_index not in embed_cache:
        embed_launch: list[str] = config.current.enabled_embeds[embed_index].split(" ")
        embed_name = embed_launch[0]
        embed_args = embed_launch[1:]

        prettyprint_args = ' '.join(embed_args)
        logging.debug(f"Loading new embed '{embed_name}' with arguments '{prettyprint_args}' into cache...", stack_info=False)

        valid_embeds: list[type[embeds.Embed]] = list(filter(lambda e: e.name() == embed_name, embeds.ALL_EMBEDS))
        assert len(valid_embeds) > 0, f"No embed named '{embed_name}' found!"
        assert len(valid_embeds) == 1, f"Multiple embeds named '{embed_name}' found!"

        embed_cache[embed_index] = valid_embeds[0](*embed_args)

    old_embed = embed # to fix threading errors
    embed = embed_cache[embed_index]
    try:
        embed.on_enable()
    except Exception as e:
        logging.dump_exception(e, cycle_embed_timer, "embedEnableFail")
    if old_embed is not None:
        try:
            old_embed.on_disable()
        except Exception as e:
            logging.dump_exception(e, cycle_embed_timer, "embedDisableFail")

    cycle_embed_timer = threading.Timer(embed.duration(), _cycle_embed)
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

