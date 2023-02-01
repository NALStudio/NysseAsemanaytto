from __future__ import annotations

import threading
from datetime import date, datetime, tzinfo
from types import EllipsisType
from typing import Final, NamedTuple

import pygame
from nalpy import math

import embeds
from core import colors, electricity, elements, font_helper, logging


class _ElectricityScale(NamedTuple):
    max_value: int
    scale_step: int
    hue_deg: int
    hue_val: float = 0.8

_scales: Final[tuple[_ElectricityScale, ...]] = ( # max_value from small => big. Recommended to be divisible by scale_step
    _ElectricityScale(0,   2, 240),
    _ElectricityScale(4,   2, 180),
    _ElectricityScale(10,  2, 120),
    _ElectricityScale(30,  5, 60),
    _ElectricityScale(50,  5, 0),
    _ElectricityScale(100, 5, 0, hue_val=0.0)
)

PADDING: Final[float] = 2.0
PRICE_HOURS_COUNT: Final[int] = 24
BAR_DEFAULT_SAT: Final[float] = 1.0
BAR_PAST_SAT: Final[float] = 0.25
NO_DATA_COLOR: Final[tuple[int, int, int]] = (128, 128, 128)

DATA_PORTION: Final[float] = 0.25 # 0.0 - 1.0

TIME_LINE_COLOUR: Final[tuple[int, int, int]] = (0, 0, 0)
TIME_LINE_WIDTH: Final[int] = 2

SCALES_COLOR: Final[tuple[int, int, int]] = (192, 192, 192)
SCALES_COLOR_DARK: Final[tuple[int, int, int]] = (64, 64, 64)
SCALES_LINE_MARGIN: Final[int] = 10
SCALES_DATA_MARGIN: Final[int] = 20

BACKGROUND_COLOR: Final[tuple[int, int, int]] = (246, 246, 246)
CARD_COLOR: Final[tuple[int, int, int]] = (252, 252, 252)

electricity_scales_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/OpenSans-Regular.ttf")
electricity_scales_bold_font: font_helper.SizedFont = font_helper.SizedFont("resources/fonts/OpenSans-Bold.ttf")

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


        max_price: electricity.ElectricityPrice = max(prices, key=lambda p: p.price)
        render_scale: _ElectricityScale = self.smallest_render_scale(max_price.price)

        surf: pygame.Surface = pygame.Surface(size)
        surf.fill(BACKGROUND_COLOR)

        data_portion_height: int = round(size[1] * DATA_PORTION)
        data_margin: int = round(data_portion_height / 6)
        data_size: tuple[int, int] = (size[0] - 2 * data_margin, data_portion_height - 2 * data_margin)
        graph_size: tuple[int, int] = (size[0], size[1] - data_portion_height)
        surf.blit(self.render_data(data_size, data_margin, prices), (data_margin, data_margin))
        surf.blit(self.render_prices(graph_size, render_scale, prices), (0, data_portion_height))

        return surf

    def render_prices(self, size: tuple[int, int], render_scale: _ElectricityScale, prices: tuple[electricity.ElectricityPrice, ...]) -> pygame.Surface:
        surf: pygame.Surface = pygame.Surface(size)
        surf.fill(BACKGROUND_COLOR)

        # Render scale lines
        scales_count: int = int(render_scale.max_value / render_scale.scale_step)
        value_per_scale: int = int(render_scale.max_value / scales_count)
        height_per_scale: float = size[1] / scales_count
        scale_iter_count: int = scales_count + 1

        font_size: int = round(size[1] / 30)
        scale_prices: list[pygame.Surface] = [electricity_scales_font.get_size(font_size).render(str(i * value_per_scale), True, SCALES_COLOR_DARK) for i in range(scale_iter_count)]
        scales_data_width: int = max(scale_prices, key=lambda s: s.get_width()).get_width()
        scales_data_width += SCALES_DATA_MARGIN

        for i in range(scale_iter_count):
            y: int = size[1] - round(height_per_scale * i)
            scale_price: pygame.Surface = scale_prices[i]
            scale_price_y: int
            if i == 0: # First price top
                scale_price_y = y - scale_price.get_height() # Align bottom with line
            elif i == (scale_iter_count - 1): # Last price at bottom
                scale_price_y = y # Align top with line
            else: # Middle prices
                scale_price_y = y - round(scale_price.get_height() / 2) # Align center with line
            surf.blit(scale_price, (scales_data_width - SCALES_DATA_MARGIN - scale_price.get_width(), scale_price_y))
            pygame.draw.line(surf, SCALES_COLOR, (scales_data_width - SCALES_LINE_MARGIN, y), (size[0], y))

        # Render price bars

        total_bar_width: float = (size[0] - scales_data_width) / PRICE_HOURS_COUNT
        for i in range(PRICE_HOURS_COUNT):
            price: electricity.ElectricityPrice | None = get_price_for_hour(i, prices)

            left: int = round((total_bar_width * i) + (PADDING / 2))
            right: int = round((total_bar_width * (i + 1)) - (PADDING / 2))
            # Calculating width by rounded right and left edges to minimize differences in padding sizes.
            bar_size: tuple[int, int] = (right - left, size[1])
            bar_pos: tuple[int, int] = (left + scales_data_width, 0)
            del left, right


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
                time_line_x: int = bar_pos[0] + bar1_width
                if TIME_LINE_WIDTH % 2 == 0: # If line has no center-point, prefer to draw one to the left instead of right.
                    time_line_x -= 1

                pygame.draw.line(surf, TIME_LINE_COLOUR, (time_line_x, 0), (time_line_x, bar_size[1]), width=TIME_LINE_WIDTH)
                now_text: pygame.Surface = electricity_scales_font.get_size(font_size).render(self._enable_time.strftime("%H:%M"), True, (0, 0, 0))
                surf.blit(now_text, (time_line_x + 2 * TIME_LINE_WIDTH, 0))
            else: # Data not in the current hour
                bar_sat: float = BAR_PAST_SAT if price.end <= self._enable_time else BAR_DEFAULT_SAT # Past or future saturation to be used
                bar: pygame.Surface = self.render_bar(price.price, render_scale, bar_sat, bar_size)
                surf.blit(bar, bar_pos)

        return surf

    def render_data(self, size: tuple[int, int], center_margin: int, prices: tuple[electricity.ElectricityPrice, ...]) -> pygame.Surface:
        surf: pygame.Surface = pygame.Surface(size)
        surf.fill(BACKGROUND_COLOR)

        day_prices: list[electricity.ElectricityPrice | None] = [get_price_for_hour(h, prices) for h in range(PRICE_HOURS_COUNT)]
        day_price_sum: float = 0.0
        day_price_count: int = 0
        now_price: float | None = None
        for hr, dp in enumerate(day_prices):
            if dp is None:
                logging.warning(f"Day price for hour {hr} could not be loaded for average.")
                continue

            if hr == self._enable_time.hour:
                now_price = dp.price

            day_price_sum += dp.price
            day_price_count += 1

        average_price: float = day_price_sum / day_price_count

        centerx: int = round(size[0] / 2)
        border_radius: int = round(size[1] / 4)
        rect1_right: int = centerx - round(center_margin / 2)
        rect2_left: int = centerx + round(center_margin / 2)
        rect1: pygame.Rect = pygame.Rect(0, 0, rect1_right, size[1])
        rect2: pygame.Rect = pygame.Rect(rect2_left, 0, size[0] - rect2_left, size[1])
        pygame.draw.rect(surf, colors.Colors.WHITE, rect1, border_radius=border_radius)
        pygame.draw.rect(surf, colors.Colors.WHITE, rect2, border_radius=border_radius)

        price_height: int = round(size[1] * 0.3)
        price_text_height: int = round(price_height / 1.5)
        price_line_height: int = round(size[1] * 0.6)
        price_text_margin: int = round(size[1] * 0.2)

        now_price_rnd = data_price_with_color(price_height, price_line_height, now_price if now_price is not None else math.NEGATIVEINFINITY)
        now_price_rnd_left: int = rect1.right - now_price_rnd.get_width() - price_text_margin
        now_text_rnd = electricity_scales_font.get_size(price_text_height).render("Hinta Nyt", True, (0, 0, 0))
        surf.blit(now_price_rnd, (now_price_rnd_left, rect1.centery - now_price_rnd.get_height() / 2))
        surf.blit(now_text_rnd, (round(math.lerp(rect1.left, now_price_rnd_left, 0.5) - now_text_rnd.get_width() / 2), rect1.centery - now_text_rnd.get_height() / 2))

        average_price_rnd = data_price_with_color(price_height, price_line_height, average_price)
        average_price_rnd_left: int = rect2.right - average_price_rnd.get_width() - price_text_margin
        average_text_rnd = electricity_scales_font.get_size(price_text_height).render("Päivän Keskiarvo", True, (0, 0, 0))
        surf.blit(average_price_rnd, (average_price_rnd_left, rect2.centery - average_price_rnd.get_height() / 2))
        surf.blit(average_text_rnd, (round(math.lerp(rect2.left, average_price_rnd_left, 0.5) - average_text_rnd.get_width() / 2), rect2.centery - average_text_rnd.get_height() / 2))

        return surf

    @staticmethod
    def render_bar(price: float, render_scale: _ElectricityScale, saturation: float, size: tuple[int, int]) -> pygame.Surface:
        height: int = round(math.remap(price, 0.0, render_scale.max_value, 0.0, size[1]))

        color: tuple[int, int, int] = ElectricityPricesEmbed._get_price_colour(price, saturation)

        return ElectricityPricesEmbed._render_bar(size, height, color)

    @staticmethod
    def _render_bar(size: tuple[int, int], height: int, color: tuple[int, int, int]) -> pygame.Surface:
        border_radius: int = round(size[0] / 4)

        rect: tuple[int, int, int, int] = (0, size[1] - height, size[0], height)
        surf: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, color, rect, border_top_left_radius=border_radius, border_top_right_radius=border_radius)

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

def data_price_with_color(ref_height: int, line_height: int, price: float) -> pygame.Surface:
    text: pygame.Surface = electricity_scales_bold_font.get_size(ref_height).render(f"{price:.2f} snt/kWh", True, (0, 0, 0))
    height: int = text.get_height()

    line_thickness: int = round(line_height * 0.2)
    line_margin: int = line_thickness
    line_x: int = text.get_width() + line_margin

    surf: pygame.Surface = pygame.Surface((line_x + line_thickness, max(height, line_height)), flags=pygame.SRCALPHA)
    surf.blit(text, (0, round(surf.get_height() / 2 - text.get_height() / 2)))

    line_rect: tuple[int, int, int, int] = (line_x, round((surf.get_height() - line_height) / 2), line_thickness, line_height)
    line_color: tuple[int, int, int] = ElectricityPricesEmbed._get_price_colour(price, BAR_DEFAULT_SAT)
    pygame.draw.rect(surf, line_color, line_rect, border_radius=round(line_thickness / 2))

    return surf

def get_price_for_hour(hour: int, prices: tuple[electricity.ElectricityPrice, ...]) -> electricity.ElectricityPrice | None:
    hours_start_index: int = prices[0].start.hour
    price_i: int = hour - hours_start_index
    price: electricity.ElectricityPrice | None = prices[price_i] if 0 <= price_i < len(prices) else None
    if price is not None:
        assert price.start.hour == hour

    return price
