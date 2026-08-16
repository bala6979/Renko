"""Render a validated config as one standalone Volrix Strategy subclass."""

from __future__ import annotations

from pathlib import Path

from .config import RenkoStrategyConfig


TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "strategies" / "volrix" / "template.py.txt"


def render_volrix_strategy(
    config: RenkoStrategyConfig, *, class_name: str = "ParameterizedRenkoSynthetic"
) -> str:
    config.validate()
    cutoff = config.execution.cutoff_time
    replacements = {
        "__CLASS_NAME__": class_name,
        "__UNDERLYING__": repr(config.underlying),
        "__TIMEFRAME__": str(config.source.timeframe_minutes),
        "__BOX_MODE__": repr(config.renko.box_mode),
        "__FIXED_POINTS__": repr(config.renko.fixed_points or 0.0),
        "__LTP_PERCENT__": repr(config.renko.ltp_percent or 0.0),
        "__ANNUAL_PERCENT__": repr(config.renko.annual_percent or 0.0),
        "__ATR_PERIOD__": str(config.renko.atr_period),
        "__ATR_MULTIPLIER__": repr(config.renko.atr_multiplier),
        "__REVERSAL_BOXES__": str(config.renko.reversal_boxes),
        "__SIGNAL_MODE__": repr(config.signal.mode),
        "__EMA_PERIOD__": str(config.signal.ema_period or 0),
        "__CONTINUATION_ANCHOR__": repr(config.signal.continuation_anchor),
        "__PULLBACK_MIN__": str(config.signal.pullback_min_boxes),
        "__PULLBACK_MAX__": str(config.signal.pullback_max_boxes),
        "__INITIAL_STOPS__": repr(tuple(_stop_dict(item) for item in config.risk.initial_stops)),
        "__TRAILING_STOPS__": repr(tuple(_stop_dict(item) for item in config.risk.trailing_stops)),
        "__EXPIRY__": repr(config.execution.expiry),
        "__LOTS__": str(config.execution.lots),
        "__POSITIONAL__": repr(config.execution.holding == "positional"),
        "__MAX_ENTRIES__": str(config.execution.max_entries_per_day or 0),
        "__CUTOFF_HOUR__": str(cutoff.hour if cutoff else -1),
        "__CUTOFF_MINUTE__": str(cutoff.minute if cutoff else -1),
        "__EXIT_HOUR__": str(config.execution.exit_time.hour),
        "__EXIT_MINUTE__": str(config.execution.exit_time.minute),
        "__TICK_SIZE__": repr(config.tick_size),
    }
    rendered = TEMPLATE_PATH.read_text(encoding="utf-8")
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered


def _stop_dict(stop: object) -> dict[str, object]:
    return {
        "type": stop.type,
        "value": stop.value,
        "multiplier": stop.multiplier,
        "boxes": stop.boxes,
    }
