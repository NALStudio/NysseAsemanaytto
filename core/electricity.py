from datetime import date, datetime, time, timedelta, tzinfo
import json
import threading
import pytz
from typing import Any, Callable, Iterable, NamedTuple, Self

from core import datetime_utils, logging

import requests


EARLIEST_FETCH_DATE: date = date(2021, 1, 1)
FINLAND_TIMEZONE = pytz.timezone("Europe/Helsinki")

def get_earliest_time_for_next_day_prices(now: datetime) -> datetime:
    finland_date: date = now.astimezone(FINLAND_TIMEZONE).date()
    finland_datetime: datetime = datetime.combine(finland_date, time(hour=14), FINLAND_TIMEZONE)
    return finland_datetime

class ElectricityPrice(NamedTuple):
    price: float
    """(euro)cent/kWh"""

    date: date
    hour: int
    """0 - 23"""

    @classmethod
    def from_day_ahead_json(cls, data: dict[str, float | str]) -> Self:
        price: float | str = data["price"]
        assert isinstance(price, float)

        start: str | float = data["startDate"]
        assert isinstance(start, str)

        start_datetime: datetime = datetime.fromisoformat(start).astimezone(FINLAND_TIMEZONE)

        return cls(price, start_datetime.date(), start_datetime.hour)

def _valid_timezone(tz: tzinfo | None) -> bool:
    if tz is None:
        return False

    now_without_timezone: datetime = datetime.now()
    finland_offset: timedelta = FINLAND_TIMEZONE.utcoffset(now_without_timezone)
    tz_offset: timedelta | None = tz.utcoffset(now_without_timezone)

    return finland_offset == tz_offset

def get_prices_for_date(date: datetime, on_finish: Callable[[date, tuple[ElectricityPrice | None, ...]], Any]):
    """Price index determines the starting hour of the given price. The end hour is the next hour from the starting hour. Method fetches the data on a separate thread. All dates are in correlation to the Finnish timezone."""
    if not _valid_timezone(date.tzinfo):
        raise ValueError("Invalid timezone.")

    provider = _ElecticityPricesRequestProvider(date.date(), on_finish)
    request_thread = threading.Thread(target=provider.get_prices_for_date, name=f"ElectricityPricesRequest", daemon=False)
    request_thread.start()

class _ElecticityPricesRequestProvider: # HACK: Passing arguments on thread start ignores type checking.
    _DAY_AHEAD_ENDPOINT: str = "https://api.porssisahko.net/v1/latest-prices.json"
    _PRICE_ENDPOINT_WITH_FORMATTABLE_DATE_AND_HOUR: str = "https://api.porssisahko.net/v1/price.json?date={date}&hour={hour}"

    def __init__(self, fetch_date: date, on_finish: Callable[[date, tuple[ElectricityPrice | None, ...]], Any]) -> None:
        self.fetch_date: date = fetch_date
        self.on_finish: Callable[[date, tuple[ElectricityPrice | None, ...]], Any] = on_finish

    def get_prices_for_date(self) -> None:
        """Prices are sorted from old to new. Method is blocking."""

        day_ahead_prices: tuple[ElectricityPrice, ...] = tuple(self._fetch_day_ahead_prices())
        """Sorted from old to new"""

        prices: list[ElectricityPrice | None] = self._get_prices(day_ahead_prices, self.fetch_date)
        for hour in range(len(prices)):
            if prices[hour] is None:
                logging.debug(f"Fetching single hour data for hour: {hour}")
                prices[hour] = self._fetch_price(self.fetch_date, hour)

        self.on_finish(self.fetch_date, tuple(prices))

    @staticmethod
    def _get_prices(day_ahead_prices: tuple[ElectricityPrice, ...], date: date) -> list[ElectricityPrice | None]:
        prices_for_date: list[ElectricityPrice | None] = [None for _ in range(24)]

        # Prices should be from old to new
        for da_price in day_ahead_prices:
            if da_price.date < date: # This day not reached yet
                continue
            if da_price.date > date: # This day's end was reached
                break

            da_index: int = da_price.hour
            assert prices_for_date[da_index] is None
            prices_for_date[da_index] = da_price

        return prices_for_date

    @staticmethod
    def _fetch_day_ahead_prices(max_retries: int = 5) -> Iterable[ElectricityPrice]:
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
            yield ElectricityPrice.from_day_ahead_json(pj)

    @staticmethod
    def _fetch_price(_date: date, hour: int, max_retries: int = 5) -> ElectricityPrice | None:
        if _date < EARLIEST_FETCH_DATE:
            raise ValueError(f"No data before: {EARLIEST_FETCH_DATE}")
        if not (0 <= hour <= 23):
            raise ValueError(f"Invalid hour: {hour}")

        endpoint: str = _ElecticityPricesRequestProvider._PRICE_ENDPOINT_WITH_FORMATTABLE_DATE_AND_HOUR.format(date=_date.isoformat(), hour=hour)

        price_json: str | None = None
        retries: int = 0
        while price_json is None:
            resp = requests.get(endpoint)
            if resp.status_code == 404:
                return None

            if resp.ok:
                price_json = resp.text
            else:
                retries += 1
                if retries > max_retries:
                    raise RuntimeError(f"Invalid response! Response below:\n{resp.content}")
