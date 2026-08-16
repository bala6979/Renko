from datetime import datetime, timedelta
from decimal import Decimal

from renko_research.bricks import Brick
from renko_research.config import RiskConfig, SignalConfig, StopConfig
from renko_research.risk import RiskManager
from renko_research.signals import SignalAction, SignalEngine


START = datetime(2026, 8, 14, 9, 20)


def brick(sequence: int, close: float, direction: int, size: float = 10) -> Brick:
    value = Decimal(str(close))
    box = Decimal(str(size))
    return Brick(
        START + timedelta(minutes=sequence),
        value - direction * box,
        value,
        direction,
        sequence,
        box,
    )


def test_no_ema_enters_initial_direction() -> None:
    engine = SignalEngine(SignalConfig(mode="reversal", ema_period=None))
    decision = engine.process([brick(1, 110, 1)])
    assert decision.action == SignalAction.ENTER_LONG


def test_ema_rejected_reversal_is_exit_only() -> None:
    engine = SignalEngine(SignalConfig(mode="reversal", ema_period=2))
    engine.process([brick(1, 100, 1), brick(2, 110, 1)])
    decision = engine.process([brick(3, 107, -1)], position_direction=1)
    assert decision.action == SignalAction.EXIT
    assert "EMA-rejected" in decision.reason


def test_last_traded_pullback_resumption() -> None:
    config = SignalConfig(
        mode="pullback_continuation",
        ema_period=None,
        continuation_anchor="last_traded_trend",
        pullback_min_boxes=1,
        pullback_max_boxes=2,
    )
    engine = SignalEngine(config)
    engine.notify_entry(1)
    engine.process([brick(1, 90, -1)])
    decision = engine.process([brick(2, 100, 1)])
    assert decision.action == SignalAction.ENTER_LONG


def test_combined_initial_stops_use_tightest_level() -> None:
    risk = RiskManager(
        RiskConfig(
            initial_stops=(
                StopConfig("entry_percent", value=1),
                StopConfig("box_offset", value=2),
            )
        )
    )
    risk.enter(1, 1000, 10)
    assert risk.active_level == 990
    assert risk.check_price_bar(1005, 989) is not None


def test_price_and_atr_trails_only_tighten() -> None:
    risk = RiskManager(
        RiskConfig(
            trailing_stops=(
                StopConfig("price_box_offset", boxes=2),
                StopConfig("atr_from_brick", multiplier=2),
            )
        )
    )
    risk.enter(1, 100, 10)
    assert risk.check_price_bar(130, 101) is None
    risk.update_price_box_trails(10)
    risk.process_bricks([brick(1, 120, 1)], atr_value=5)
    assert risk.active_level == 110
    risk.update_price_box_trails(20)
    assert risk.active_level == 110


def test_opposite_box_tsl_is_completed_box_exit() -> None:
    risk = RiskManager(
        RiskConfig(trailing_stops=(StopConfig("opposite_boxes", boxes=2),))
    )
    risk.enter(1, 100, 10)
    assert risk.process_bricks([brick(1, 90, -1)], atr_value=None) is None
    hit = risk.process_bricks([brick(2, 80, -1)], atr_value=None)
    assert hit is not None
    assert "opposite-box" in hit.reason


def test_three_brick_sph_spl_marks_alternating_pivots_and_breaks_out() -> None:
    engine = SignalEngine(
        SignalConfig(
            mode="sph_spl",
            ema_period=None,
            pivot_confirmation_boxes=3,
        )
    )

    decision = engine.process(
        [brick(1, 110, 1), brick(2, 100, -1), brick(3, 90, -1), brick(4, 80, -1)]
    )
    assert decision.action == SignalAction.NONE
    assert engine.sph == 110
    assert [pivot.kind for pivot in engine.last_pivots] == ["SPH"]

    engine.process([brick(5, 90, 1), brick(6, 100, 1), brick(7, 110, 1)])
    assert engine.spl == 80
    decision = engine.process([brick(8, 120, 1)])
    assert decision.action == SignalAction.ENTER_LONG
    assert decision.direction == 1
    assert "SPH breakout" in decision.reason


def test_sph_spl_break_reverses_an_existing_position() -> None:
    engine = SignalEngine(
        SignalConfig(mode="sph_spl", pivot_confirmation_boxes=3)
    )
    engine.process(
        [brick(1, 110, 1), brick(2, 100, -1), brick(3, 90, -1), brick(4, 80, -1)]
    )
    engine.process([brick(5, 90, 1), brick(6, 100, 1), brick(7, 110, 1)])
    decision = engine.process([brick(8, 70, -1)], position_direction=1)
    assert decision.action == SignalAction.REVERSE_SHORT
    assert decision.direction == -1


def test_sph_spl_level_is_consumed_after_one_breakout() -> None:
    engine = SignalEngine(
        SignalConfig(mode="sph_spl", pivot_confirmation_boxes=3)
    )
    engine.process(
        [brick(1, 110, 1), brick(2, 100, -1), brick(3, 90, -1), brick(4, 80, -1)]
    )
    engine.process([brick(5, 90, 1), brick(6, 100, 1), brick(7, 110, 1)])
    first = engine.process([brick(8, 120, 1)])
    second = engine.process([brick(9, 130, 1)])
    assert first.action == SignalAction.ENTER_LONG
    assert second.action == SignalAction.NONE
