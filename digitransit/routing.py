from typing import Any, Callable, Generator, Sequence, TypeVar
from digitransit.enums import Mode, RealtimeState
import json
import requests
from datetime import datetime

_T = TypeVar("_T")


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
    def __init__(self, name: str, vehicleMode: str | None, stoptimesWithoutPatterns: Sequence[dict[str, Any]]) -> None:
        self.name: str = name
        self.vehicleMode: Mode | None = Mode(vehicleMode) if vehicleMode is not None else None

        self.stoptimes: list[Stoptime] = [Stoptime(**stoptime) for stoptime in stoptimesWithoutPatterns]

class Route:
    def __init__(self, shortName: str | None, longName: str | None, mode: str | None) -> None:
        self.shortName: str | None = shortName
        self.longName: str | None = longName
        self.mode: Mode | None = Mode(mode) if mode is not None else None

class Trip:
    def __init__(self, route: dict[str, Any]) -> None:
        self.route: Route = Route(**route)

class Alert:
    def __init__(self, feed: str | None, alertHeaderText: str | None, alertDescriptionText: str, route: dict[str, Any] | None) -> None:
        self.feed: str | None = feed
        self.alertHeaderText: str | None = alertHeaderText
        self.alertDescriptionText: str = alertDescriptionText
        self.route: Route | None = Route(**route) if route is not None else None


def get_stop_info(endpoint: str, stopcode: int, numberOfDepartures: int | None = None) -> Stop:
    query = """{
  stop(id: "tampere:STOPID") {
    name
    vehicleMode
    stoptimesWithoutPatternsNUMDEPARTS {
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
        route {
          shortName
          longName
          mode
        }
      }
    }
  }
}
""".replace("STOPID", f"{stopcode:04d}").replace("NUMDEPARTS", f"(numberOfDepartures: {numberOfDepartures})" if numberOfDepartures is not None else "")

    return _make_request(endpoint, query, "stop", Stop)

def get_alerts(endpoint: str) -> list[Alert]:
    query = """{
  alerts(feeds:["tampere"]) {
    feed
    alertHeaderText
    alertDescriptionText
    route {
      shortName
      longName
      mode
    }
  }
}
"""

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
      raise ValueError(f"No data found! Expected data with key: {expected_data_key}")

    return constructor(**keydata)
