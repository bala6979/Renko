from datetime import datetime

from renko_research.config import RenkoStrategyConfig
from renko_research.engine import RenkoStrategyEngine
from renko_research.execution import nearest_strike
from renko_research.market import Candle
from renko_research.rollover import FuturesStateBook


def config(**execution_overrides) -> RenkoStrategyConfig:
    execution = {"expiry": "monthly", "holding": "positional"}
    execution.update(execution_overrides)
    return RenkoStrategyConfig.from_mapping(
        {
            "underlying": "NIFTY",
            "source": {"timeframe_minutes": 5},
            "renko": {
                "box_mode": "fixed_points",
                "fixed_points": 10,
                "reversal_boxes": 1,
            },
            "signal": {"mode": "reversal", "ema_period": None},
            "risk": {"initial_stops": [{"type": "entry_percent", "value": 1}]},
            "execution": execution,
        }
    )


def candle(at: str, close: float, high: float | None = None, low: float | None = None) -> Candle:
    timestamp = datetime.fromisoformat(at)
    return Candle(timestamp, close, high or close, low or close, close, "NIFTYFUT")


def test_engine_emits_two_leg_synthetic_entry() -> None:
    engine = RenkoStrategyEngine(config())
    engine.process_source_candle(candle("2026-08-14T09:20:00", 25000))
    engine.process_source_candle(candle("2026-08-14T09:25:00", 25015))
    assert engine.position_direction == 1
    assert len(engine.intents) == 2
    assert {item.side for item in engine.intents} == {"buy", "sell"}
    assert {item.option_type for item in engine.intents} == {"CE", "PE"}


def test_price_stop_is_checked_before_new_source_signal() -> None:
    engine = RenkoStrategyEngine(config())
    engine.process_source_candle(candle("2026-08-14T09:20:00", 1000))
    engine.process_source_candle(candle("2026-08-14T09:25:00", 1015))
    events = engine.process_minute(
        candle("2026-08-14T09:26:00", 1005, high=1010, low=1000)
    )
    assert any(event.kind == "exit" for event in events)
    assert engine.position_direction == 0


def test_intraday_exit_precedes_stop() -> None:
    engine = RenkoStrategyEngine(config(holding="intraday"))
    engine.process_source_candle(candle("2026-08-14T15:20:00", 1000))
    engine.process_source_candle(candle("2026-08-14T15:25:00", 1015))
    events = engine.process_minute(
        candle("2026-08-14T15:28:00", 900, high=1000, low=800)
    )
    exits = [event for event in events if event.kind == "exit"]
    assert exits[0].details["reason"] == "intraday 15:28 exit"


def test_roll_rebase_preserves_direction() -> None:
    engine = RenkoStrategyEngine(config())
    engine.process_source_candle(candle("2026-08-14T09:20:00", 1000))
    engine.process_source_candle(candle("2026-08-14T09:25:00", 1015))
    engine.rebase_after_futures_roll(
        datetime(2026, 8, 27, 15, 28), 1025, 10
    )
    assert engine.position_direction == 1
    assert engine.risk.entry_price == 1025


def test_state_book_promotes_warmed_next_contract() -> None:
    book = FuturesStateBook(dict)
    book.set_contracts("AUG", "SEP")
    book.state("SEP")["bricks"] = 12
    promoted = book.promote("OCT")
    assert promoted["bricks"] == 12
    assert book.current_contract == "SEP"


def test_nearest_strikes() -> None:
    assert nearest_strike("NIFTY", 24726) == 24750
    assert nearest_strike("BANKNIFTY", 54341) == 54300
