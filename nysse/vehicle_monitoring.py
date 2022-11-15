from typing import Callable, NamedTuple, Self, TypeVar
from xml.etree import ElementTree
import base64

import requests

_T = TypeVar("_T")

_ENDPOINT = "https://data.waltti.fi/tampere/api/sirirealtime/v1.3/ws"

default_namespaces: dict[str, str] = { "siri": "http://www.siri.org.uk/siri" }

def _find_element(element: ElementTree.Element, path: str) -> ElementTree.Element:
    find: ElementTree.Element | None = element.find("siri:" + path, default_namespaces)
    if find is None:
        raise ValueError(f"Path '{path}' not found in element.")
    return find

def _find_all_elements(element: ElementTree.Element, path: str, add_namespace: bool = False) -> list[ElementTree.Element]:
    if add_namespace:
        path = "siri:" + path
    return element.findall(path, default_namespaces)

def _find_str(element: ElementTree.Element, path: str) -> str:
    find: ElementTree.Element = _find_element(element, path)
    text: str | None = find.text
    if text is None or len(text) < 1:
        raise ValueError(f"No value specified in path: '{path}'")

    return text

def _find_int(element: ElementTree.Element, path: str) -> int:
    return __find_type(element, path, int)

def _find_float(element: ElementTree.Element, path: str) -> float:
    return __find_type(element, path, float)

def _find_bool(element: ElementTree.Element, path: str) -> bool:
    text = _find_str(element, path)
    if text == "true":
        return True
    if text == "false":
        return False
    raise ValueError(f"Cannot parse '{text}' into bool.")

def __find_type(element: ElementTree.Element, path: str, constructor: Callable[[str], _T]) -> _T:
    text = _find_str(element, path)

    value: _T
    try:
        value = constructor(text)
    except ValueError:
        raise ValueError(f"Value '{text}' could not be converted to object with the specified constructor.")

    return value

class Coordinate(NamedTuple):
    latitude: float
    longitude: float

    @classmethod
    def from_xml_element(cls, element: ElementTree.Element) -> Self:
        lat: float = _find_float(element, "Latitude")
        lon: float = _find_float(element, "Longitude")

        return cls(latitude=lat, longitude=lon)

class MonitoredVehicleJourney(NamedTuple):
    line_ref: str
    direction_ref: int

    origin_name: str
    origin_shortname: str
    """Should match digitransit's stop code."""

    destination_name: str
    destination_shortname: str
    """Should match digitransit's stop code."""

    monitored: bool
    vehicle_location: Coordinate
    bearing: float

    @classmethod
    def from_xml_element(cls, element: ElementTree.Element) -> Self:
        return cls(
            line_ref=_find_str(element, "LineRef"),
            direction_ref=_find_int(element, "DirectionRef"),

            origin_name=_find_str(element, "OriginName"),
            origin_shortname=_find_str(element, "OriginShortName"),

            destination_name=_find_str(element, "DestinationName"),
            destination_shortname=_find_str(element, "DestinationShortName"),

            monitored=_find_bool(element, "Monitored"),
            vehicle_location=Coordinate.from_xml_element(_find_element(element, "VehicleLocation")),
            bearing=_find_float(element, "Bearing")
        )

def get_monitored_vehicle_journeys(client_id: str, client_secret: str, line_ref: str) -> tuple[MonitoredVehicleJourney, ...]:
    query: str = f"""
<?xml version="1.0" encoding="UTF-8"?>
<Siri xmlns="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.3" xsi:schemaLocation="http://www.kizoom.com/standards/siri/schema/1.3/siri.xsd">
	<ServiceRequest>
		<VehicleMonitoringRequest version="1.3">
			<LineRef>{line_ref}</LineRef>
		</VehicleMonitoringRequest>
	</ServiceRequest>
</Siri>
""".strip()

    def _constructor(delivery: ElementTree.Element) -> tuple[MonitoredVehicleJourney, ...]:
        elements: list[ElementTree.Element] = _find_all_elements(delivery, ".//siri:MonitoredVehicleJourney", add_namespace=False)
        return tuple(MonitoredVehicleJourney.from_xml_element(e) for e in elements)

    return _make_request(client_id, client_secret, query, _constructor)

def _get_auth(client_id: str, client_secret: str) -> str:
    raw_str: str = f"{client_id}:{client_secret}"
    b64_bytes: bytes = base64.b64encode(bytes(raw_str, encoding="utf-8"))
    b64: str = b64_bytes.decode("utf-8")
    return f"Basic {b64}"

def _make_request(client_id: str, client_secret: str, query_xml: str, constructor: Callable[[ElementTree.Element], _T]) -> _T:
    headers: dict[str, str] = {
        "content-type": "application/xml",
        "Authorization": _get_auth(client_id, client_secret)
    }

    response = requests.post(_ENDPOINT, query_xml, headers=headers)
    if not response.ok:
        raise RuntimeError(f"Invalid response! Response below:\n{response.content.decode('utf-8')}")

    root = ElementTree.fromstring(response.content)
    assert root.tag.endswith("Siri")

    return constructor(_find_element(root, "ServiceDelivery"))
