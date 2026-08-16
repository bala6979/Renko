from pathlib import Path

import pytest

from renko_research.config import RenkoStrategyConfig, load_config


ROOT = Path(__file__).resolve().parents[1]


def test_example_configs_are_valid() -> None:
    assert load_config(ROOT / "configs" / "nifty.yaml").underlying == "NIFTY"
    assert load_config(ROOT / "configs" / "banknifty.yaml").underlying == "BANKNIFTY"
    assert (
        load_config(ROOT / "configs" / "samples" / "banknifty_fixed_reversal.yaml").renko.box_mode
        == "fixed_points"
    )


def test_banknifty_rejects_weekly_execution() -> None:
    with pytest.raises(ValueError, match="monthly"):
        RenkoStrategyConfig.from_mapping(
            {
                "underlying": "BANKNIFTY",
                "renko": {"box_mode": "fixed_points", "fixed_points": 50},
                "execution": {"expiry": "weekly"},
            }
        )


def test_invalid_mode_specific_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="ltp_percent"):
        RenkoStrategyConfig.from_mapping(
            {"underlying": "NIFTY", "renko": {"box_mode": "ltp_percent"}}
        )


def test_ema_regime_continuation_requires_ema() -> None:
    with pytest.raises(ValueError, match="requires ema_period"):
        RenkoStrategyConfig.from_mapping(
            {
                "underlying": "NIFTY",
                "renko": {"box_mode": "fixed_points", "fixed_points": 10},
                "signal": {
                    "mode": "pullback_continuation",
                    "ema_period": None,
                    "continuation_anchor": "ema_regime",
                },
            }
        )
