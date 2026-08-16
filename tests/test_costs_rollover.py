from datetime import datetime

import pytest

from renko_research.config import RenkoStrategyConfig
from renko_research.costs import option_order_charges
from renko_research.engine import RenkoStrategyEngine
from renko_research.market import Candle


def test_option_charges_apply_sell_stt_and_buy_stamp() -> None:
    sell = option_order_charges(side="sell", premium=100, quantity=130)
    buy = option_order_charges(side="buy", premium=100, quantity=130)
    assert sell.stt == 19.5
    assert sell.stamp == 0
    assert buy.stt == 0
    assert buy.stamp == pytest.approx(0.39)
    assert sell.gst == pytest.approx((20 + 6.5 + 0.013) * 0.18)


def fixed_config() -> RenkoStrategyConfig:
    return RenkoStrategyConfig.from_mapping(
        {
            "underlying": "NIFTY",
            "renko": {
                "box_mode": "fixed_points",
                "fixed_points": 10,
                "reversal_boxes": 1,
            },
            "signal": {"ema_period": None},
            "risk": {
                "initial_stops": [{"type": "entry_percent", "value": 1}]
            },
        }
    )


def bar(at: str, close: float) -> Candle:
    return Candle(datetime.fromisoformat(at), close, close, close, close, "FUT")


def test_promote_warmed_chart_preserves_position_and_rebases_risk() -> None:
    current = RenkoStrategyEngine(fixed_config())
    next_contract = RenkoStrategyEngine(fixed_config())
    current.process_source_candle(bar("2026-08-20T09:20:00", 1000))
    current.process_source_candle(bar("2026-08-20T09:25:00", 1015))
    next_contract.warm_source_candle(bar("2026-08-20T09:20:00", 1020))
    next_contract.warm_source_candle(bar("2026-08-20T09:25:00", 1045))

    current.promote_warmed_chart(
        next_contract,
        timestamp=datetime(2026, 8, 27, 15, 28),
        futures_price=1045,
    )
    assert current.position_direction == 1
    assert current.renko.last_close == next_contract.renko.last_close
    assert current.risk.entry_price == 1045
    assert current.risk.active_level == pytest.approx(1034.55)
