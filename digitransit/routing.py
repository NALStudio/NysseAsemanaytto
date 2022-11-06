from typing import Any, Callable, Generator, Iterable, Sequence, TypeVar
from digitransit.enums import Mode, RealtimeState
import json
import requests
from datetime import datetime

_T = TypeVar("_T")


class Alert:
    def __init__(self, feed: str | None, alertHeaderText: str | None, alertDescriptionText: str, route: dict[str, Any] | None, stop: dict[str, Any] | None) -> None:
        self.feed: str | None = feed
        self.alertHeaderText: str | None = alertHeaderText
        self.alertDescriptionText: str = alertDescriptionText
        self.route: Route | None = Route(**route) if route is not None else None
        self.stop: Stop | None = Stop(**stop) if stop is not None else None

class Stoptime:
    def __init__(self, scheduledArrival: int | None, realtimeArrival: int | None, arrivalDelay: int | None, scheduledDeparture: int | None, realtimeDeparture: int | None, departureDelay: int | None, realtime: bool | None, realtimeState: str | None, serviceDay: int | None, headsign: str | None, trip: dict[str, Any] | None) -> None:
        self.scheduledArrival: datetime | None = datetime.fromtimestamp(serviceDay + scheduledArrival) if scheduledArrival is not None and serviceDay is not None else None
        self.realtimeArrival: datetime | None = datetime.fromtimestamp(serviceDay + realtimeArrival) if realtimeArrival is not None and serviceDay is not None else None
        self.arrivalDelay: int | None = arrivalDelay
        self.scheduledDeparture: datetime | None = datetime.fromtimestamp(serviceDay + scheduledDeparture) if scheduledDeparture is not None and serviceDay is not None else None
        self.realtimeDeparture: datetime | None = datetime.fromtimestamp(serviceDay + realtimeDeparture) if realtimeDeparture is not None and serviceDay is not None else None
        self.departureDelay: int | None = departureDelay
        self.realtime: bool | None = realtime
        self.realtimeState: RealtimeState | None = RealtimeState(realtimeState)
        self.headsign: str | None = headsign
        self.trip: Trip | None = Trip(**trip) if trip is not None else None

class Stop:
    def __init__(self, gtfsId: str, name: str, vehicleMode: str | None, stoptimesWithoutPatterns: Sequence[dict[str, Any]] | None = None) -> None:
        self.gtfsId: str = gtfsId
        self.name: str = name
        self.vehicleMode: Mode | None = Mode(vehicleMode) if vehicleMode is not None else None

        self.stoptimes: list[Stoptime] | None = None
        if stoptimesWithoutPatterns is not None:
            self.stoptimes = [Stoptime(**stoptime) for stoptime in stoptimesWithoutPatterns]

class Route:
    def __init__(self, gtfsId: str, shortName: str | None, longName: str | None, mode: str | None, stops: Sequence[dict[str, Any]] | None = None) -> None:
        self.gtfsId: str = gtfsId
        self.shortName: str | None = shortName
        self.longName: str | None = longName
        self.mode: Mode | None = Mode(mode) if mode is not None else None

        self.stops: list[Stop] | None = None
        if stops is not None:
            self.stops = [Stop(**stop) for stop in stops]

class Trip:
    def __init__(self, gtfsId: str, route: dict[str, Any]) -> None:
        self.gtfsId: str = gtfsId
        self.route: Route = Route(**route)


def get_stop_info(endpoint: str, stop_gtfsId: str, numberOfDepartures: int | None = None, omitNonPickups: bool | None = None) -> Stop:
    query = """{
  stop(STOPARGS) {
    gtfsId
    name
    vehicleMode
    stoptimesWithoutPatterns(TIMESARGS) {
      scheduledArrival
      realtimeArrival
      arrivalDelay
      scheduledDeparture
      realtimeDeparture
      departureDelay
      realtime
      realtimeState
      serviceDay
      headsign
      trip {
        gtfsId
        route {
          gtfsId
          shortName
          longName
          mode
        }
      }
    }
  }
}
"""
    query = _replace_with_arguments(query, "(STOPARGS)", ("id", stop_gtfsId))
    query = _replace_with_arguments(query, "(TIMESARGS)", ("numberOfDepartures", numberOfDepartures), ("omitNonPickups", omitNonPickups))

    return _make_request(endpoint, query, "stop", Stop)

def get_alerts(endpoint: str, feeds: list[str] | tuple[str, ...]) -> list[Alert]: # Apparently Sequence[str] allows the user to put in a bare string
    query = """{
  alerts(ALERTSARGS) {
    feed
    alertHeaderText
    alertDescriptionText
    stop {
      gtfsId
      name
      vehicleMode
    }
    route {
      gtfsId
      shortName
      longName
      mode
      stops {
        gtfsId
        name
        vehicleMode
      }
    }
  }
}
"""
    query = _replace_with_arguments(query, "(ALERTSARGS)", ("feeds", feeds))

    def constructor(data: dict[str, list[dict[str, Any]]]) -> list[Alert]:
        return [Alert(**params) for params in data["alerts"]]

    return _make_request(endpoint, query, None, constructor)


def _make_request(endpoint: str, query: str, expected_data_key: str | None, constructor: Callable[..., _T]) -> _T:
    jsonString = "{\"query\": " + json.dumps(query) + "}"

    response = requests.post(endpoint, jsonString, headers={"content-type": "application/json"})
    if not response.ok:
        raise RuntimeError(f"Invalid response! Response below:\n{response.content}")

    d = json.loads(response.content)
    data = d["data"]
    keydata = d if expected_data_key is None else data[expected_data_key]
    if keydata is None:
      raise ValueError(f"No data found! Expected data with key: {expected_data_key}. Response below:\n{response.content}")

    return constructor(**keydata)

def _replace_with_arguments(query: str, keyword: str, *args: tuple[str, object | None]) -> str:
    """None argument value is default."""
    formatted_args: list[str] = []
    for name, value in args:
        if value is None:
            continue
        formatted_value: str = json.dumps(value, indent=None)
        formatted_args.append(f"{name}:{formatted_value}")

    output: str
    if len(formatted_args) > 0:
        output = f"({','.join(formatted_args)})"
    else:
        output = ""

    return query.replace(keyword, output)
