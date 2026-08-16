"""Validated configuration for the common Renko framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_TIMEFRAMES = {1, 2, 3, 5, 10, 15, 20, 25, 30, 45, 60, 120, 240}
BOX_MODES = {"fixed_points", "ltp_percent", "atr", "annual_percent"}
SIGNAL_MODES = {"reversal", "pullback_continuation", "sph_spl"}
CONTINUATION_ANCHORS = {"last_traded_trend", "ema_regime"}
INITIAL_STOP_TYPES = {"entry_percent", "box_offset"}
TRAILING_STOP_TYPES = {"atr_from_brick", "opposite_boxes", "price_box_offset"}


def _positive(value: float | int | None, name: str) -> None:
    if value is None or value <= 0:
        raise ValueError(f"{name} must be positive")


def _parse_time(value: str | None, name: str) -> time | None:
    if value is None:
        return None
    try:
        hour, minute = (int(part) for part in value.split(":"))
        return time(hour, minute)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must use HH:MM") from exc


@dataclass(frozen=True, slots=True)
class SourceConfig:
    timeframe_minutes: int = 5
    candle_input: str = "close"
    signal_contract: str = "front_month_futures"
    rollover_policy: str = "warm_next_preserve_rebase"

    def validate(self) -> None:
        if self.timeframe_minutes not in SUPPORTED_TIMEFRAMES:
            raise ValueError("unsupported source timeframe")
        if self.candle_input != "close":
            raise ValueError("only close-based Renko is supported")
        if self.signal_contract != "front_month_futures":
            raise ValueError("signal contract must be front_month_futures")
        if self.rollover_policy != "warm_next_preserve_rebase":
            raise ValueError("unsupported futures rollover policy")


@dataclass(frozen=True, slots=True)
class RenkoConfig:
    box_mode: str
    fixed_points: float | None = None
    ltp_percent: float | None = None
    annual_percent: float | None = None
    atr_period: int = 14
    atr_multiplier: float = 1.0
    reversal_boxes: int = 2

    def validate(self) -> None:
        if self.box_mode not in BOX_MODES:
            raise ValueError("unsupported Renko box mode")
        _positive(self.reversal_boxes, "reversal_boxes")
        if self.box_mode == "fixed_points":
            _positive(self.fixed_points, "fixed_points")
        elif self.box_mode == "ltp_percent":
            _positive(self.ltp_percent, "ltp_percent")
        elif self.box_mode == "annual_percent":
            _positive(self.annual_percent, "annual_percent")
        elif self.box_mode == "atr":
            _positive(self.atr_period, "atr_period")
            _positive(self.atr_multiplier, "atr_multiplier")


@dataclass(frozen=True, slots=True)
class SignalConfig:
    mode: str = "reversal"
    ema_period: int | None = None
    continuation_anchor: str = "ema_regime"
    pullback_min_boxes: int = 1
    pullback_max_boxes: int = 3
    pivot_confirmation_boxes: int = 3

    def validate(self) -> None:
        if self.mode not in SIGNAL_MODES:
            raise ValueError("unsupported signal mode")
        if self.ema_period is not None:
            _positive(self.ema_period, "ema_period")
        if self.continuation_anchor not in CONTINUATION_ANCHORS:
            raise ValueError("unsupported continuation anchor")
        _positive(self.pullback_min_boxes, "pullback_min_boxes")
        if self.pullback_max_boxes < self.pullback_min_boxes:
            raise ValueError("pullback_max_boxes must be >= pullback_min_boxes")
        _positive(self.pivot_confirmation_boxes, "pivot_confirmation_boxes")
        if self.mode == "pullback_continuation":
            if self.continuation_anchor == "ema_regime" and self.ema_period is None:
                raise ValueError("ema_regime continuation requires ema_period")


@dataclass(frozen=True, slots=True)
class StopConfig:
    type: str
    value: float | None = None
    multiplier: float | None = None
    boxes: int | None = None

    def validate(self, *, trailing: bool) -> None:
        allowed = TRAILING_STOP_TYPES if trailing else INITIAL_STOP_TYPES
        if self.type not in allowed:
            raise ValueError(f"unsupported {'trailing' if trailing else 'initial'} stop")
        if self.type in {"entry_percent", "box_offset"}:
            _positive(self.value, f"{self.type}.value")
        elif self.type == "atr_from_brick":
            _positive(self.multiplier, "atr_from_brick.multiplier")
        else:
            _positive(self.boxes, f"{self.type}.boxes")


@dataclass(frozen=True, slots=True)
class RiskConfig:
    initial_stops: tuple[StopConfig, ...] = ()
    trailing_stops: tuple[StopConfig, ...] = ()

    def validate(self) -> None:
        for stop in self.initial_stops:
            stop.validate(trailing=False)
        for stop in self.trailing_stops:
            stop.validate(trailing=True)


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    instrument: str = "synthetic_futures"
    expiry: str = "monthly"
    lots: int = 2
    holding: str = "positional"
    max_entries_per_day: int | None = None
    entry_cutoff: str | None = None
    intraday_exit: str = "15:28"

    def validate(self, underlying: str) -> None:
        if self.instrument != "synthetic_futures":
            raise ValueError("execution instrument must be synthetic_futures")
        if self.expiry not in {"weekly", "monthly"}:
            raise ValueError("expiry must be weekly or monthly")
        if underlying == "BANKNIFTY" and self.expiry != "monthly":
            raise ValueError("BANKNIFTY supports monthly synthetic contracts only")
        _positive(self.lots, "lots")
        if self.holding not in {"intraday", "positional"}:
            raise ValueError("holding must be intraday or positional")
        if self.max_entries_per_day is not None:
            _positive(self.max_entries_per_day, "max_entries_per_day")
        _parse_time(self.entry_cutoff, "entry_cutoff")
        _parse_time(self.intraday_exit, "intraday_exit")

    @property
    def cutoff_time(self) -> time | None:
        return _parse_time(self.entry_cutoff, "entry_cutoff")

    @property
    def exit_time(self) -> time:
        result = _parse_time(self.intraday_exit, "intraday_exit")
        assert result is not None
        return result


@dataclass(frozen=True, slots=True)
class RenkoStrategyConfig:
    underlying: str
    source: SourceConfig
    renko: RenkoConfig
    signal: SignalConfig = field(default_factory=SignalConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    tick_size: float = 0.05

    def validate(self) -> "RenkoStrategyConfig":
        if self.underlying not in {"NIFTY", "BANKNIFTY"}:
            raise ValueError("underlying must be NIFTY or BANKNIFTY")
        _positive(self.tick_size, "tick_size")
        self.source.validate()
        self.renko.validate()
        self.signal.validate()
        self.risk.validate()
        self.execution.validate(self.underlying)
        if any(stop.type == "atr_from_brick" for stop in self.risk.trailing_stops):
            _positive(self.renko.atr_period, "atr_period")
            _positive(self.renko.atr_multiplier, "atr_multiplier")
        return self

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "RenkoStrategyConfig":
        risk_data = data.get("risk", {})
        config = cls(
            underlying=str(data["underlying"]).upper(),
            source=SourceConfig(**data.get("source", {})),
            renko=RenkoConfig(**data["renko"]),
            signal=SignalConfig(**data.get("signal", {})),
            risk=RiskConfig(
                initial_stops=tuple(
                    StopConfig(**item) for item in risk_data.get("initial_stops", [])
                ),
                trailing_stops=tuple(
                    StopConfig(**item) for item in risk_data.get("trailing_stops", [])
                ),
            ),
            execution=ExecutionConfig(**data.get("execution", {})),
            tick_size=float(data.get("tick_size", 0.05)),
        )
        return config.validate()


def load_config(path: str | Path) -> RenkoStrategyConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("configuration root must be a mapping")
    return RenkoStrategyConfig.from_mapping(data)
