import datetime
import digitransit.routing
from typing import NamedTuple


class UpdateContext(NamedTuple):
    time: datetime.datetime
    stopinfo: digitransit.routing.Stop
