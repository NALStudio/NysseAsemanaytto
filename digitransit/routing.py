from digitransit.enums import Mode, RealtimeState
import json
import requests

class Stoptime:
    def __init__(self, **kwargs) -> None:
        self.scheduledArrival: int = kwargs["scheduledArrival"]
        self.realtimeArrival: int = kwargs["realtimeArrival"]
        self.arrivalDelay: int = kwargs["arrivalDelay"]
        self.scheduledDeparture: int = kwargs["scheduledDeparture"]
        self.realtimeDeparture: int = kwargs["realtimeDeparture"]
        self.departureDelay: int = kwargs["departureDelay"]
        self.realtime: bool = kwargs["realtime"]
        self.realtimeState: RealtimeState = RealtimeState(kwargs["realtimeState"])
        self.serviceDay: int = kwargs["serviceDay"]
        self.headsign: str = kwargs["headsign"]
        self.trip: Trip = Trip(**kwargs["trip"])

class Stop:
    def __init__(self, **kwargs) -> None:
        self.name: str = kwargs["name"]
        self.vehicleMode: Mode = Mode(kwargs["vehicleMode"])

        self.stoptimes = [Stoptime(**stoptime) for stoptime in kwargs["stoptimesWithoutPatterns"]]

class Trip:
    def __init__(self, **kwargs) -> None:
        self.routeShortName: str = kwargs["routeShortName"]

def get_stop_info(endpoint: str, stopcode: int) -> Stop:
    query = """{
  stop(id: "tampere:STOPID") {
    name
    vehicleMode
    stoptimesWithoutPatterns {
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
        routeShortName
      }
    }
  }
}
""".replace("STOPID", f"{stopcode:04d}")

    jsonString = "{\"query\": " + json.dumps(query) + "}"

    response = requests.post(endpoint, jsonString, headers={"content-type": "application/json"})
    if not response.ok:
        raise RuntimeError(f"Invalid response! Response below:\n{response.content}")

    d = json.loads(response.content)
    if d["data"]["stop"] == None:
      raise ValueError("Invalid stopcode!")
    return Stop(**d["data"]["stop"])