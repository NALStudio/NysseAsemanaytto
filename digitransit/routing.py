from digitransit.enums import Endpoint, Mode, RealtimeState
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

class Stop:
    def __init__(self, **kwargs) -> None:
        self.name: str = kwargs["name"]
        self.vehicleMode: Mode = Mode(kwargs["vehicleMode"])

        self.stoptimes = [Stoptime(**stoptime) for stoptime in kwargs["stoptimesWithoutPatterns"]]


def get_stop_info(endpoint: Endpoint, stopcode: int) -> Stop:
    url = f"https://api.digitransit.fi/routing/v1/routers/{endpoint.value}/index/graphql"

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
                }
            }
            }""".replace("STOPID", f"{stopcode:04d}")

    jsonString = "{\"query\": " + json.dumps(query) + "}"

    response = requests.post(url, jsonString, headers={"content-type": "application/json"})
    if not response.ok:
        raise RuntimeError(f"Invalid response! Response below:\n{response.content}")

    d = json.loads(response.content)
    return Stop(**d["data"]["stop"])