from datetime import date, datetime, time, timedelta, tzinfo
import json
import threading
from typing import Any, Callable, Iterable, NamedTuple, Self

import requests


class ElectricityPrice(NamedTuple):
    price: float # (euro)cent/ kWh
    start: datetime
    end: datetime

    @classmethod
    def from_json(cls, data: dict[str, float | str], tzinfo: tzinfo | None) -> Self:
        price: float | str = data["price"]
        assert isinstance(price, float)

        start: str | float = data["startDate"]
        assert isinstance(start, str)

        end: str | float = data["endDate"]
        assert isinstance(end, str)

        start_datetime: datetime = datetime.fromisoformat(start).astimezone(tzinfo)
        end_datetime: datetime = datetime.fromisoformat(end).astimezone(tzinfo)

        return cls(price, start_datetime, end_datetime)

def get_prices_for_date(date: date, tzinfo: tzinfo, on_finish: Callable[[date, tuple[ElectricityPrice, ...]], Any]):
    """Prices are sorted from old to new. Method fetches the data on a separate thread."""
    provider = _ElecticityPricesRequestProvider(date, tzinfo, on_finish)
    request_thread = threading.Thread(target=provider.get_prices_for_date, name=f"ElectricityPricesRequest", daemon=False)
    request_thread.start()

class _ElecticityPricesRequestProvider: # HACK: Passing arguments on thread start ignores type checking.
    _DAY_AHEAD_ENDPOINT: str = "https://api.porssisahko.net/v1/latest-prices.json"

    def __init__(self, fetch_date: date, timezone: tzinfo, on_finish: Callable[[date, tuple[ElectricityPrice]], Any]) -> None:
        self.fetch_date: date = fetch_date
        self.timezone: tzinfo = timezone
        self.on_finish: Callable[[date, tuple[ElectricityPrice, ...]], Any] = on_finish

    def get_prices_for_date(self) -> None:
        """Prices are sorted from new to old. Method is blocking."""

        day_ahead_prices: tuple[ElectricityPrice, ...] = tuple(self._fetch_day_ahead_prices(self.timezone, 5))
        """Sorted from old to new"""

        prices: tuple[ElectricityPrice, ...] = self._get_prices(day_ahead_prices, self.fetch_date, self.timezone)
        self.on_finish(self.fetch_date, prices)

    @staticmethod
    def _get_prices(day_ahead_prices: tuple[ElectricityPrice, ...], date: date, tzinfo: tzinfo) -> tuple[ElectricityPrice, ...]:
        first_start_datetime: datetime = datetime.combine(date, time(0, 0, 0, 0, tzinfo))
        last_end_datetime: datetime = first_start_datetime + timedelta(days=1)

        prices_for_date: tuple[ElectricityPrice, ...] = tuple(filter(lambda ep: ep.start >= first_start_datetime and ep.end <= last_end_datetime, day_ahead_prices))
        prices_count: int = len(prices_for_date)

        for index in range(1, prices_count):
            assert day_ahead_prices[index - 1].end == day_ahead_prices[index].start
            # Order is from old to new so last ends when next starts

        return prices_for_date

    @staticmethod
    def _fetch_day_ahead_prices(tzinfo: tzinfo, max_retries: int) -> Iterable[ElectricityPrice]:
        prices_json: str | None = None
        retries: int = 0
        while prices_json is None:
            resp = requests.get(_ElecticityPricesRequestProvider._DAY_AHEAD_ENDPOINT)
            if resp.ok:
                prices_json = resp.text
            else:
                retries += 1
                if retries > max_retries:
                    raise RuntimeError(f"Invalid response! Response below:\n{resp.content}")

        prices: list[dict[str, float | str]] = json.loads(prices_json)["prices"]
        for pj in reversed(prices): # Prices are given by the API from new to old, reverse it.
            yield ElectricityPrice.from_json(pj, tzinfo)

