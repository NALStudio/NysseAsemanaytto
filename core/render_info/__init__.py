from core import config as _config
from core import logging as _logging
import digitransit.routing as _routing
import threading as _threading
import core.render_info.embeds as _embed_render_info

from core.render_info.embeds import CurrentEmbedData as CurrentEmbedData


def get_stop_gtfsId() -> str:
    return f"tampere:{_config.current.stopcode:04d}"

stopinfo: _routing.Stop

def update_stopinfo() -> None:
    global stopinfo
    _logging.info("Fetching stop info...", stack_info=False)
    try:
        stopinfo = _routing.get_stop_info(_config.current.endpoint, get_stop_gtfsId(), _config.current.departure_count, _config.current.omit_non_pickups, _config.current.omit_canceled)
    except Exception as e:
        _logging.dump_exception(e, _threading.current_thread(), "requestFail")

current_embed_data: CurrentEmbedData | None = None
current_embed_data_lock: _threading.Lock = _threading.Lock()

def start_embed_cycling():
    _embed_render_info.start_embed_cycling()

def stop_embed_cycling():
    _embed_render_info.stop_embed_cycling()
