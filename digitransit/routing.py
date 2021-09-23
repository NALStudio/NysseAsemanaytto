from typing import Any, Dict, List, Optional, Sequence
from digitransit.enums import Mode, RealtimeState
import json
import requests

class Stoptime:
    def __init__(self, scheduledArrival: int, realtimeArrival: int, arrivalDelay: int, scheduledDeparture: int, realtimeDeparture: int, departureDelay: int, realtime: bool, realtimeState: str, serviceDay: int, headsign: str, trip: Dict[str, Any]) -> None:
        self.scheduledArrival: int = scheduledArrival
        self.realtimeArrival: int = realtimeArrival
        self.arrivalDelay: int = arrivalDelay
        self.scheduledDeparture: int = scheduledDeparture
        self.realtimeDeparture: int = realtimeDeparture
        self.departureDelay: int = departureDelay
        self.realtime: bool = realtime
        self.realtimeState: RealtimeState = RealtimeState(realtimeState)
        self.serviceDay: int = serviceDay
        self.headsign: str = headsign
        self.trip: Trip = Trip(**trip)

class Stop:
    def __init__(self, name: str, vehicleMode: str, stoptimesWithoutPatterns: Sequence[Dict[str, Any]]) -> None:
        self.name: str = name
        self.vehicleMode: Mode = Mode(vehicleMode)

        self.stoptimes = [Stoptime(**stoptime) for stoptime in stoptimesWithoutPatterns]

class Trip:
    def __init__(self, routeShortName: str) -> None:
        self.routeShortName: str = routeShortName

def get_stop_info(endpoint: str, stopcode: int, numberOfDepartures: Optional[int] = None) -> Stop:
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
        routeShortName
      }
    }
  }
}
""".replace("STOPID", f"{stopcode:04d}").replace("NUMDEPARTS", f"(numberOfDepartures: {numberOfDepartures})" if numberOfDepartures != None else "")

    jsonString = "{\"query\": " + json.dumps(query) + "}"

    response = requests.post(endpoint, jsonString, headers={"content-type": "application/json"})
    if not response.ok:
        raise RuntimeError(f"Invalid response! Response below:\n{response.content}")

    d = json.loads(response.content)
    if d["data"]["stop"] == None:
      raise ValueError("Invalid stopcode!")
    return Stop(**d["data"]["stop"])