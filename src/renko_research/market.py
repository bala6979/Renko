"""Market data primitives and session-aligned candle aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    symbol: str = ""

    def __post_init__(self) -> None:
        if self.high < max(self.open, self.close) or self.low > min(
            self.open, self.close
        ):
            raise ValueError("invalid OHLC candle")
        if self.high < self.low:
            raise ValueError("candle high must not be below low")


class CandleAggregator:
    """Aggregate one-minute candles into exchange-session buckets.

    Input timestamps identify minute starts. Emitted timestamps identify the
    end of the completed aggregate candle.
    """

    def __init__(
        self,
        timeframe_minutes: int,
        *,
        session_start: time = time(9, 15),
        session_end: time = time(15, 30),
    ) -> None:
        if timeframe_minutes <= 0:
            raise ValueError("timeframe must be positive")
        self.timeframe = timeframe_minutes
        self.session_start = session_start
        self.session_end = session_end
        self._key: tuple[date, int] | None = None
        self._candles: list[Candle] = []

    def _bucket_key(self, candle: Candle) -> tuple[date, int] | None:
        day = candle.timestamp.date()
        start = datetime.combine(day, self.session_start, candle.timestamp.tzinfo)
        end = datetime.combine(day, self.session_end, candle.timestamp.tzinfo)
        if candle.timestamp < start or candle.timestamp >= end:
            return None
        minute = int((candle.timestamp - start).total_seconds() // 60)
        return day, minute // self.timeframe

    def update(self, candle: Candle) -> Candle | None:
        key = self._bucket_key(candle)
        if key is None:
            return None
        completed = None
        if self._key is not None and key != self._key:
            completed = self._emit()
        self._key = key
        self._candles.append(candle)
        return completed

    def flush(self) -> Candle | None:
        if not self._candles:
            return None
        return self._emit()

    def _emit(self) -> Candle:
        candles = self._candles
        first = candles[0]
        last = candles[-1]
        timestamp = last.timestamp + timedelta(minutes=1)
        aggregate = Candle(
            timestamp=timestamp,
            open=first.open,
            high=max(item.high for item in candles),
            low=min(item.low for item in candles),
            close=last.close,
            symbol=last.symbol,
        )
        self._candles = []
        return aggregate
