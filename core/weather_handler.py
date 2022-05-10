from dataclasses import dataclass
import datetime
import threading
import time as time_module
import fmiopendata.multipoint
from typing import Any, Callable, Generator

import pygame

@dataclass
class Weather:
    time_utc: datetime.datetime
    time_local: datetime.datetime
    temperature: float
    symbol_id: int

@dataclass
class WeatherFetchParams:
    duration: datetime.timedelta
    timestep_minutes: int | None = None

_cached_symbols: dict[int, pygame.surface.Surface] = {}
def get_weather_symbol(symbol_id: int) -> pygame.surface.Surface:
    """
    Get the texture of the weather symbol.
    """
    if symbol_id not in _cached_symbols:
        _cached_symbols[symbol_id] = pygame.image.load(f"resources/textures/weather_symbols/png/{symbol_id}.png").convert_alpha()
    return _cached_symbols[symbol_id]

def get_weather(fmi_place: str, params: WeatherFetchParams, on_finish: Callable[[tuple[Weather]], Any]) -> None:
    """
    Get weather data from FMI.
    """
    provider = _WeatherRequestProvider(fmi_place, params, on_finish)
    request_thread = threading.Thread(target=provider.get_weather, name=f"WeatherRequest_{fmi_place}")
    request_thread.start()

def _utc2local(utc: datetime.datetime) -> datetime.datetime:
    epoch = time_module.mktime(utc.timetuple())
    offset = datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)
    return utc + offset

class _WeatherRequestProvider: # HACK: Passing arguments on thread start ignores type checking.
    def __init__(self, fmi_place: str, params: WeatherFetchParams, on_finish: Callable[[tuple[Weather]], Any]) -> None:
        self.fmi_place: str = fmi_place
        self.params: WeatherFetchParams = params
        self.on_finish: Callable[[tuple[Weather]], Any] = on_finish

    def _parse_multipoint(self, mp: fmiopendata.multipoint.MultiPoint) -> Generator[Weather, None, None]:
        datapoints = list(mp.data.items())

        for dp in datapoints:
            time: datetime.datetime
            data: dict[str, dict[str, dict[str, Any]]]
            time, data = dp
            assert isinstance(time, datetime.datetime)

            assert len(data) == 1
            inner_data = list(data.values())[0]

            temperature = inner_data["Air temperature"]
            assert temperature["units"] == "degC"
            temperature = temperature["value"]
            assert isinstance(temperature, float)

            symbol = inner_data["Weather"]
            assert symbol["units"] == "index"
            symbol = symbol["value"]
            assert isinstance(symbol, float)
            symbol = int(symbol)

            local_time = _utc2local(time) # Slow to call each parsing, but this shit is threaded anyways :D
            wt = Weather(time, local_time, temperature, symbol)
            yield wt

    def get_weather(self) -> None:
        utcnow: datetime.datetime = datetime.datetime.utcnow()
        starttime = utcnow.replace(minute=0, second=0, microsecond=0)
        endtime: datetime.datetime = starttime + self.params.duration

        DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%SZ"
        starttime_str: str = starttime.strftime(DATETIME_FORMAT)
        endtime_str: str = endtime.strftime(DATETIME_FORMAT)

        args = [ "parameters=Temperature,WeatherSymbol3" ]
        if self.params.timestep_minutes is not None:
            args.append(f"timestep={self.params.timestep_minutes}")

        mp = fmiopendata.multipoint.download_and_parse(
            "fmi::forecast::harmonie::surface::point::multipointcoverage",
            (f"starttime={starttime_str}", f"endtime={endtime_str}", f"place={self.fmi_place}", "&".join(args))
        )
        parsed = self._parse_multipoint(mp)

        self.on_finish(tuple(parsed)) # Converting to a tuple so that we don't iterate between threads and such
