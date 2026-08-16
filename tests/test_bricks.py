from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from renko_research.bricks import RenkoBuilder
from renko_research.sizing import percentage_brick, prior_atr_brick


START = datetime(2026, 8, 14, 9, 15)


def test_initial_close_seeds_without_emitting_a_brick() -> None:
    builder = RenkoBuilder(10)
    assert builder.update(START, 25000) == []
    assert builder.last_close == Decimal("25000")


def test_multi_brick_move_uses_only_completed_close() -> None:
    builder = RenkoBuilder(10, initial_price=25000)
    bricks = builder.update(START, 25035)
    assert [brick.close for brick in bricks] == [
        Decimal("25010"),
        Decimal("25020"),
        Decimal("25030"),
    ]
    assert all(brick.timestamp == START for brick in bricks)
    assert all(brick.box_size == Decimal("10") for brick in bricks)


def test_box_size_can_change_without_rebasing_last_close() -> None:
    builder = RenkoBuilder(10, initial_price=100)
    first = builder.update(START, 112)
    second = builder.update(
        START + timedelta(minutes=1), 122, brick_size=5
    )
    assert [brick.close for brick in first] == [Decimal("110")]
    assert [brick.close for brick in second] == [Decimal("115"), Decimal("120")]
    assert [brick.box_size for brick in second] == [Decimal("5"), Decimal("5")]


def test_reversal_confirmation_is_configurable() -> None:
    builder = RenkoBuilder(10, initial_price=100, reversal_bricks=2)
    builder.update(START, 110)
    assert builder.update(START + timedelta(minutes=1), 95) == []
    reversed_bricks = builder.update(START + timedelta(minutes=2), 90)
    assert [brick.close for brick in reversed_bricks] == [Decimal("100"), Decimal("90")]
    assert all(brick.direction == -1 for brick in reversed_bricks)


def test_invalid_settings_are_rejected() -> None:
    with pytest.raises(ValueError):
        RenkoBuilder(0)
    with pytest.raises(ValueError):
        RenkoBuilder(10, reversal_bricks=0)


def test_brick_size_helpers_round_to_market_tick() -> None:
    assert percentage_brick(25000, 0.1, 0.05) == Decimal("25.00")
    assert prior_atr_brick(123.4, 0.75, 0.05) == Decimal("92.55")
