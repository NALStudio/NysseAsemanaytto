from __future__ import annotations
from datetime import date, datetime, tzinfo
import threading
from types import EllipsisType
from typing import Final, NamedTuple

import pygame
from core import elements, electricity, colors, logging

from nalpy import math

import embeds

class _ElectricityScale(NamedTuple):
    max_value: int
    hue_deg: int
    hue_val: float = 0.8

_scales: Final[tuple[_ElectricityScale, ...]] = ( # Max value from small => big
    _ElectricityScale(0,   240),
    _ElectricityScale(5,   180),
    _ElectricityScale(15,  120),
    _ElectricityScale(30,  60),
    _ElectricityScale(50,  0),
    _ElectricityScale(100, 0, hue_val=0.0)
)

PADDING: Final[float] = 1.0
PRICE_HOURS_COUNT: Final[int] = 24
BAR_DEFAULT_SAT: Final[float] = 1.0
BAR_PAST_SAT: Final[float] = 0.25
NO_DATA_COLOR: Final[tuple[int, int, int]] = (128, 128, 128)

TIME_LINE_COLOUR: Final[tuple[int, int, int]] = (0, 0, 0)
TIME_LINE_WIDTH: Final[int] = 2

BACKGROUND_COLOR = colors.Colors.WHITE

class ElectricityPricesEmbed(embeds.Embed):
    def __init__(self):
        self.price_lock: threading.Lock = threading.Lock()
        self.prices: tuple[electricity.ElectricityPrice, ...] | None = None
        """Ordered from old to new."""

        self.prices_date: date | None = None

        self.rerender: bool = False

    def _set_prices(self, date: date, prices: tuple[electricity.ElectricityPrice, ...]):
        assert len(prices) > 0
        with self.price_lock:
            if self.prices is None:
                self.prices = prices

            max_existing_index: int = len(self.prices) - 1
            while max_existing_index >= 0 and self.prices[max_existing_index].end >= prices[0].end: # While latest data from max is newer or as old as than oldest price data.
                max_existing_index -= 1

            self.prices = self.prices[:(max_existing_index + 1)] + prices
            self.prices = tuple(filter(lambda ep: ep.start.date() >= date, self.prices))

        self.rerender = True


    def on_enable(self):
        now: datetime = datetime.now().astimezone(None) # Add timezone info to now call
        self._enable_time: datetime = now

        local_date: date = now.date()
        now_timezone: tzinfo | None = now.tzinfo
        assert now_timezone is not None
        if self.prices_date is None or self.prices_date != local_date:
            logging.info(f"Loading new electricity pricing data...", stack_info=False)
            electricity.get_prices_for_date(local_date, now_timezone, self._set_prices)
            self.prices_date = local_date

    def on_disable(self):
        pass

    def update(self, context: embeds.EmbedContext) -> bool | EllipsisType:
        if self.rerender:
            self.rerender = False
            # Update is single-threaded so flag can be set after check because no other threads should set this as False.
            return True

        return context.first_frame

    def render(self, size: tuple[int, int], flags: elements.RenderFlags) -> pygame.Surface | None:
        flags.clear_background = False # No need to clear background because surface is solid

        prices: tuple[electricity.ElectricityPrice] | None
        with self.price_lock:
            prices = self.prices

        if prices is None:
            logging.debug("Electricity price data is not loaded yet! Cancelling electricity price embed rendering...", stack_info=False)
            return None

        surf: pygame.Surface = pygame.Surface(size)
        surf.fill(BACKGROUND_COLOR)

        surf.blit(self.render_prices(size, prices), (0, 0))

        return surf

    def render_prices(self, size: tuple[int, int], prices: tuple[electricity.ElectricityPrice, ...]) -> pygame.Surface:
        surf: pygame.Surface = pygame.Surface(size)
        surf.fill(BACKGROUND_COLOR)

        max_price: electricity.ElectricityPrice = max(prices, key=lambda p: p.price)
        render_scale: _ElectricityScale = self.smallest_render_scale(max_price.price)

        hours_start_index: int = prices[0].start.hour
        for i in range(PRICE_HOURS_COUNT):
            price_i: int = i - hours_start_index
            price: electricity.ElectricityPrice | None = prices[price_i] if 0 <= price_i < len(prices) else None

            total_bar_width: float = size[0] / PRICE_HOURS_COUNT
            left: int = round((total_bar_width * i) + (PADDING / 2))
            right: int = round((total_bar_width * (i + 1)) - (PADDING / 2))
            # Calculating width by rounded right and left edges to minimize differences in padding sizes.
            bar_size: tuple[int, int] = (right - left, size[1])
            bar_pos: tuple[int, int] = (left, 0)


            if price is None: # No data
                bar: pygame.Surface = self._render_bar(bar_size, int(bar_size[1] * 0.8), NO_DATA_COLOR)
                surf.blit(bar, bar_pos)
            elif price.start < self._enable_time < price.end: # Data on the current hour (split into past and future bars)
                bar1_width: int = round(math.remap(self._enable_time.timestamp(), price.start.timestamp(), price.end.timestamp(), 0.0, bar_size[0]))

                bar1: pygame.Surface = self.render_bar(price.price, render_scale, BAR_PAST_SAT, (bar1_width, bar_size[1]))
                bar2: pygame.Surface = self.render_bar(price.price, render_scale, BAR_DEFAULT_SAT, (bar_size[0] - bar1_width, bar_size[1]))

                surf.blit(bar1, bar_pos)
                surf.blit(bar2, (bar_pos[0] + bar1_width, bar_pos[1]))

                # Draw line for current time
                time_line_x: int = bar_pos[0] + bar1_width #- round(TIME_LINE_WIDTH / 2) I think pygame moves the line automatically
                pygame.draw.line(surf, TIME_LINE_COLOUR, (time_line_x, 0), (time_line_x, bar_size[1]), width=TIME_LINE_WIDTH)

            else: # Data not in the current hour
                bar_sat: float = BAR_PAST_SAT if price.end <= self._enable_time else BAR_DEFAULT_SAT # Past or future saturation to be used
                bar: pygame.Surface = self.render_bar(price.price, render_scale, bar_sat, bar_size)
                surf.blit(bar, bar_pos)

        return surf

    @staticmethod
    def render_bar(price: float, render_scale: _ElectricityScale, saturation: float, size: tuple[int, int]) -> pygame.Surface:
        height: int = round(math.remap(price, 0.0, render_scale.max_value, 0.0, size[1]))

        color: tuple[int, int, int] = ElectricityPricesEmbed._get_price_colour(price, saturation)

        return ElectricityPricesEmbed._render_bar(size, height, color)

    @staticmethod
    def _render_bar(size: tuple[int, int], height: int, color: tuple[int, int, int]) -> pygame.Surface:
        rect: tuple[int, int, int, int] = (0, size[1] - height, size[0], height)
        surf: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, color, rect)

        return surf

    @staticmethod
    def _get_price_colour(price: float, saturation: float) -> tuple[int, int, int]:
        low_scale: _ElectricityScale | None
        high_scale: _ElectricityScale | None
        low_scale, high_scale = ElectricityPricesEmbed.price_falls_between_scales(price)

        if low_scale is None: # Below minimum scale
            assert high_scale is not None
            return colors.hsv2rgb(high_scale.hue_deg, saturation, high_scale.hue_val)
        elif high_scale is None: # Above maximum scale
            return colors.hsv2rgb(low_scale.hue_deg, saturation, low_scale.hue_val)
        else: # In normal scale range
            price_t: float = math.remap01(price, low_scale.max_value, high_scale.max_value)
            color_hue: float = math.lerp(low_scale.hue_deg, high_scale.hue_deg, price_t)
            color_value: float = math.lerp(low_scale.hue_val, high_scale.hue_val, price_t)
            return colors.hsv2rgb(color_hue, saturation, color_value)

    @staticmethod
    def _smallest_render_scale_index(price: float) -> int | None:
        for i, s in enumerate(_scales):
            if price > s.max_value:
                continue

            return i

    @staticmethod
    def smallest_render_scale(price: float) -> _ElectricityScale:
        i: int | None = ElectricityPricesEmbed._smallest_render_scale_index(price)
        if i is not None:
            return _scales[i]
        else:
            return _scales[-1] # Upperbound hit.

    @staticmethod
    def price_falls_between_scales(price: float) -> tuple[_ElectricityScale | None, _ElectricityScale | None]:
        i: int | None = ElectricityPricesEmbed._smallest_render_scale_index(price)
        if i is not None:
            if i == 0:
                return (None, _scales[i])
            else:
                return (_scales[i - 1], _scales[i])
        else:
            return (_scales[-1], None) # Upperbound hit.

    @staticmethod
    def name() -> str:
        return "electricity_prices"

    def requested_duration(self) -> float:
        return 15.0
