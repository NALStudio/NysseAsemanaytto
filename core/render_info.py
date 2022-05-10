import random
import string
from core import colors
from core import config
from embeds import Embed
import digitransit.routing
import traceback
import threading

#region Stop info
stopinfo: digitransit.routing.Stop
fetch_stopinfo_timer: threading.Timer | None

def generate_thread_id(prefix: str, id_length: int = 4) -> str:
    return prefix + "".join(random.choices(string.ascii_uppercase + string.digits, k=id_length))

def _fetch_stop_info() -> None:
    global stopinfo, fetch_stopinfo_timer
    print(colors.ConsoleColors.CYAN + "Fetching stop info..." + colors.ConsoleColors.RESET)
    try:
        stopinfo = digitransit.routing.get_stop_info(config.current.endpoint, config.current.stopcode, config.current.departure_count)
    except Exception as e:
        print(colors.ConsoleColors.RED + "An error occured while fetching stop info! Exception below:")
        print(colors.ConsoleColors.YELLOW + f"{type(e).__name__}: {e}")
        print(traceback.format_exc() + colors.ConsoleColors.RESET)
    if config.current.poll_rate > 0:
        fetch_stopinfo_timer = threading.Timer(config.current.poll_rate, _fetch_stop_info)
        fetch_stopinfo_timer.name = generate_thread_id("StopInfoTimer_")
        fetch_stopinfo_timer.start()

def start_stop_info_fetch() -> None:
    _fetch_stop_info()
    try:
        _ = stopinfo
    except NameError:
        raise RuntimeError("Initial stop info fetch failed!")
#endregion

#region Embed cycle
embed: Embed | None
embed_index: int = -1
cycle_embed_timer: threading.Timer | None

embed_cache: dict[int, Embed] = {}

def _cycle_embed() -> None:
    global embed, embed_index, cycle_embed_timer
    print(colors.ConsoleColors.MAGENTA + "Switching embed..." + colors.ConsoleColors.RESET)
    if len(config.current.enabled_embeds) < 1:
        print(colors.ConsoleColors.MAGENTA + "No embeds enabled! Cancelling embed cycling..." + colors.ConsoleColors.RESET)
        embed = None
        cycle_embed_timer = None
        return

    embed_index = (embed_index + 1) % len(config.current.enabled_embeds)

    if embed_index not in embed_cache:
        embed_launch: list[str] = config.current.enabled_embeds[embed_index].split(" ")
        embed_name = embed_launch[0]
        embed_args = embed_launch[1:]

        prettyprint_args = ' '.join(embed_args)
        print(f"Loading new embed '{embed_name}' with arguments '{prettyprint_args}' into cache...")

        valid_embeds: list[type[Embed]] = list(filter(lambda e: e.name() == embed_name, Embed.__subclasses__()))
        assert len(valid_embeds) > 0, f"No embed named '{embed_name}' found!"
        assert len(valid_embeds) == 1, f"Multiple embeds named '{embed_name}' found!"

        embed_cache[embed_index] = valid_embeds[0](*embed_args)

    embed = embed_cache[embed_index]
    embed.on_enable()

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

