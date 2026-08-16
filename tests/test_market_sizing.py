from datetime import datetime, timedelta
from decimal import Decimal

from renko_research.market import Candle, CandleAggregator
from renko_research.sizing import BoxSizer


def candle(timestamp: datetime, close: float, high: float | None = None, low: float | None = None) -> Candle:
    return Candle(
        timestamp,
        close,
        close if high is None else high,
        close if low is None else low,
        close,
        "NIFTY26AUGFUT",
    )


def test_five_minute_aggregation_is_session_aligned() -> None:
    aggregator = CandleAggregator(5)
    start = datetime(2026, 8, 14, 9, 15)
    emitted = []
    for offset in range(6):
        result = aggregator.update(candle(start + timedelta(minutes=offset), 100 + offset))
        if result:
            emitted.append(result)
    assert len(emitted) == 1
    assert emitted[0].timestamp == datetime(2026, 8, 14, 9, 20)
    assert emitted[0].open == 100
    assert emitted[0].close == 104


def test_ltp_size_uses_previous_completed_close() -> None:
    sizer = BoxSizer(mode="ltp_percent", tick_size=0.05, ltp_percent=1)
    first = candle(datetime(2026, 1, 2, 9, 20), 100)
    second = candle(datetime(2026, 1, 2, 9, 25), 120)
    assert sizer.process(first) is None
    assert sizer.size_before(second) == Decimal("1.00")
    sizer.observe(second)
    third = candle(datetime(2026, 1, 2, 9, 30), 90)
    assert sizer.size_before(third) == Decimal("1.20")


def test_atr_size_is_lagged_by_one_bar() -> None:
    sizer = BoxSizer(
        mode="atr", tick_size=0.05, atr_period=2, atr_multiplier=1
    )
    first = candle(datetime(2026, 1, 2, 9, 20), 100, 102, 98)
    second = candle(datetime(2026, 1, 2, 9, 25), 101, 103, 99)
    third = candle(datetime(2026, 1, 2, 9, 30), 110, 112, 100)
    assert sizer.process(first) is None
    assert sizer.process(second) is None
    assert sizer.size_before(third) == Decimal("4.00")


def test_annual_size_uses_prior_year_close_and_stays_frozen() -> None:
    sizer = BoxSizer(
        mode="annual_percent", tick_size=0.05, annual_percent=1
    )
    prior = candle(datetime(2025, 12, 31, 15, 30), 25000)
    assert sizer.process(prior) is None
    january = candle(datetime(2026, 1, 2, 9, 20), 26000)
    december = candle(datetime(2026, 12, 31, 15, 30), 30000)
    assert sizer.size_before(january) == Decimal("250.00")
    sizer.observe(january)
    assert sizer.size_before(december) == Decimal("250.00")
