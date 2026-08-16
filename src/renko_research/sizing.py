"""Leakage-safe brick-size policies."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from .market import Candle


def percentage_brick(reference_price: float, percentage: float, tick: float) -> Decimal:
    if reference_price <= 0 or percentage <= 0 or tick <= 0:
        raise ValueError("reference_price, percentage, and tick must be positive")
    raw = Decimal(str(reference_price)) * Decimal(str(percentage)) / Decimal("100")
    return _round_to_tick(raw, Decimal(str(tick)))


def prior_atr_brick(prior_session_atr: float, multiplier: float, tick: float) -> Decimal:
    """Use only an ATR finalized before the session being traded."""
    if prior_session_atr <= 0 or multiplier <= 0 or tick <= 0:
        raise ValueError("prior_session_atr, multiplier, and tick must be positive")
    raw = Decimal(str(prior_session_atr)) * Decimal(str(multiplier))
    return _round_to_tick(raw, Decimal(str(tick)))


def _round_to_tick(value: Decimal, tick: Decimal) -> Decimal:
    ticks = (value / tick).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return ticks * tick


@dataclass(slots=True)
class WilderATR:
    period: int
    value: Decimal | None = None
    previous_close: Decimal | None = None
    count: int = 0
    _seed_total: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("ATR period must be positive")

    @property
    def ready(self) -> bool:
        return self.count >= self.period and self.value is not None

    def update(self, candle: Candle) -> Decimal | None:
        high = Decimal(str(candle.high))
        low = Decimal(str(candle.low))
        close = Decimal(str(candle.close))
        true_range = high - low
        if self.previous_close is not None:
            true_range = max(
                true_range,
                abs(high - self.previous_close),
                abs(low - self.previous_close),
            )
        self.count += 1
        if self.count <= self.period:
            self._seed_total += true_range
            if self.count == self.period:
                self.value = self._seed_total / Decimal(self.period)
        else:
            assert self.value is not None
            self.value = (
                self.value * Decimal(self.period - 1) + true_range
            ) / Decimal(self.period)
        self.previous_close = close
        return self.value


class BoxSizer:
    """Return the size known before a candle, then observe that candle."""

    def __init__(
        self,
        *,
        mode: str,
        tick_size: float,
        fixed_points: float | None = None,
        ltp_percent: float | None = None,
        annual_percent: float | None = None,
        atr_period: int = 14,
        atr_multiplier: float = 1.0,
    ) -> None:
        self.mode = mode
        self.tick = Decimal(str(tick_size))
        self.fixed_points = fixed_points
        self.ltp_percent = ltp_percent
        self.annual_percent = annual_percent
        self.atr_multiplier = Decimal(str(atr_multiplier))
        self.atr = WilderATR(atr_period)
        self.previous_close: Decimal | None = None
        self.last_close_by_year: dict[int, Decimal] = {}

    def size_before(self, candle: Candle) -> Decimal | None:
        if self.mode == "fixed_points":
            return _round_to_tick(Decimal(str(self.fixed_points)), self.tick)
        if self.mode == "ltp_percent":
            if self.previous_close is None:
                return None
            return percentage_brick(
                float(self.previous_close), float(self.ltp_percent), float(self.tick)
            )
        if self.mode == "atr":
            if not self.atr.ready:
                return None
            assert self.atr.value is not None
            return _round_to_tick(self.atr.value * self.atr_multiplier, self.tick)
        if self.mode == "annual_percent":
            reference = self.last_close_by_year.get(candle.timestamp.year - 1)
            if reference is None:
                return None
            return percentage_brick(
                float(reference), float(self.annual_percent), float(self.tick)
            )
        raise ValueError(f"unsupported box mode: {self.mode}")

    def observe(self, candle: Candle) -> None:
        close = Decimal(str(candle.close))
        self.atr.update(candle)
        self.previous_close = close
        self.last_close_by_year[candle.timestamp.year] = close

    def process(self, candle: Candle) -> Decimal | None:
        size = self.size_before(candle)
        self.observe(candle)
        return size

