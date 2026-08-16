"""Configuration-driven Renko strategy orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

from .bricks import Brick, RenkoBuilder
from .config import RenkoStrategyConfig
from .execution import (
    SyntheticExitIntent,
    SyntheticLegIntent,
    synthetic_entry_intents,
)
from .market import Candle, CandleAggregator
from .risk import RiskManager
from .signals import SignalAction, SignalDecision, SignalEngine
from .sizing import BoxSizer


@dataclass(frozen=True, slots=True)
class EngineEvent:
    timestamp: datetime
    kind: str
    details: dict[str, Any]


class RenkoStrategyEngine:
    """Process futures data and emit synthetic execution intents.

    Price stops are checked against one-minute candles before newly completed
    source-candle signals. New trailing levels become active on the next minute,
    avoiding an unknowable high/low path within one candle.
    """

    def __init__(self, config: RenkoStrategyConfig) -> None:
        self.config = config.validate()
        self.aggregator = CandleAggregator(config.source.timeframe_minutes)
        self.sizer = BoxSizer(
            mode=config.renko.box_mode,
            tick_size=config.tick_size,
            fixed_points=config.renko.fixed_points,
            ltp_percent=config.renko.ltp_percent,
            annual_percent=config.renko.annual_percent,
            atr_period=config.renko.atr_period,
            atr_multiplier=config.renko.atr_multiplier,
        )
        self.renko = RenkoBuilder(
            1,
            reversal_bricks=config.renko.reversal_boxes,
        )
        self.signals = SignalEngine(config.signal)
        self.risk = RiskManager(config.risk)
        self.position_direction = 0
        self.entries_today = 0
        self.current_day: date | None = None
        self.events: list[EngineEvent] = []
        self.intents: list[SyntheticLegIntent | SyntheticExitIntent] = []
        self.last_box_size: float | None = None

    def process_minute(self, candle: Candle) -> list[EngineEvent]:
        start = len(self.events)
        self._new_day(candle.timestamp.date())
        if (
            self.config.execution.holding == "intraday"
            and self.position_direction
            and candle.timestamp.time() >= self.config.execution.exit_time
        ):
            self._exit(candle.timestamp, "intraday 15:28 exit")
            return self.events[start:]

        if self.position_direction:
            hit = self.risk.check_price_bar(candle.high, candle.low)
            if hit is not None:
                self._exit(candle.timestamp, f"{hit.reason} level={hit.level:.2f}")
                return self.events[start:]

        completed = self.aggregator.update(candle)
        if completed is not None:
            self.process_source_candle(completed)
        return self.events[start:]

    def process_source_candle(self, candle: Candle) -> list[EngineEvent]:
        start = len(self.events)
        self._new_day(candle.timestamp.date())
        size = self.sizer.size_before(candle)
        atr_before = (
            float(self.sizer.atr.value)
            if self.sizer.atr.ready and self.sizer.atr.value is not None
            else None
        )
        self.sizer.observe(candle)
        if size is None:
            self._record(candle.timestamp, "warmup_skip", candle=asdict(candle))
            return self.events[start:]

        self.last_box_size = float(size)
        bricks = self.renko.update(
            candle.timestamp,
            candle.close,
            brick_size=size,
        )
        self._record(
            candle.timestamp,
            "source_candle",
            candle=asdict(candle),
            box_size=float(size),
            atr=atr_before,
            bricks=[self._brick_dict(item) for item in bricks],
        )
        if not bricks:
            if self.position_direction:
                self.risk.update_price_box_trails(float(size))
            return self.events[start:]

        decision = self.signals.process(
            bricks,
            position_direction=self.position_direction,
        )
        if decision.action != SignalAction.NONE:
            self._apply_decision(candle, bricks[-1], decision)
        elif self.position_direction:
            tsl_hit = self.risk.process_bricks(bricks, atr_value=atr_before)
            if tsl_hit is not None:
                self._exit(candle.timestamp, tsl_hit.reason)

        if self.position_direction:
            self.risk.update_price_box_trails(float(size))
        return self.events[start:]

    def end_session(self) -> list[EngineEvent]:
        completed = self.aggregator.flush()
        if completed is not None:
            self.process_source_candle(completed)
        if (
            completed is not None
            and self.config.execution.holding == "intraday"
            and self.position_direction
        ):
            self._exit(completed.timestamp, "intraday session-end fallback")
        return self.events

    def rebase_after_futures_roll(
        self, timestamp: datetime, futures_price: float, box_size: float
    ) -> None:
        if self.position_direction:
            self.risk.rebase(futures_price, box_size)
        self._record(
            timestamp,
            "futures_roll_rebase",
            direction=self.position_direction,
            futures_price=futures_price,
            box_size=box_size,
        )

    def warm_source_candle(self, candle: Candle) -> list[Brick]:
        """Advance a non-traded contract chart for later rollover promotion."""
        size = self.sizer.size_before(candle)
        self.sizer.observe(candle)
        if size is None:
            return []
        self.last_box_size = float(size)
        bricks = self.renko.update(
            candle.timestamp, candle.close, brick_size=size
        )
        if bricks:
            self.signals.process(bricks, position_direction=0)
        return bricks

    def promote_warmed_chart(
        self,
        warmed: "RenkoStrategyEngine",
        *,
        timestamp: datetime,
        futures_price: float,
    ) -> None:
        """Promote independently warmed chart state and preserve trade direction."""
        annual_closes = dict(self.sizer.last_close_by_year)
        annual_closes.update(warmed.sizer.last_close_by_year)
        warmed.sizer.last_close_by_year = annual_closes
        self.sizer = warmed.sizer
        self.renko = warmed.renko
        self.signals = warmed.signals
        self.last_box_size = warmed.last_box_size
        if self.position_direction:
            self.signals.notify_entry(self.position_direction)
            if self.last_box_size is None:
                raise ValueError("warmed contract has no usable box size")
            self.risk.rebase(futures_price, self.last_box_size)
        self._record(
            timestamp,
            "futures_chart_promoted",
            direction=self.position_direction,
            futures_price=futures_price,
            box_size=self.last_box_size,
        )

    def _apply_decision(
        self, candle: Candle, brick: Brick, decision: SignalDecision
    ) -> None:
        if decision.action == SignalAction.EXIT:
            self._exit(candle.timestamp, decision.reason)
            return
        if decision.action in {SignalAction.REVERSE_LONG, SignalAction.REVERSE_SHORT}:
            self._exit(candle.timestamp, decision.reason)
            self._enter(candle, brick, decision.direction, decision.reason)
            return
        if decision.action in {SignalAction.ENTER_LONG, SignalAction.ENTER_SHORT}:
            self._enter(candle, brick, decision.direction, decision.reason)

    def _can_enter(self, timestamp: datetime) -> bool:
        maximum = self.config.execution.max_entries_per_day
        if maximum is not None and self.entries_today >= maximum:
            return False
        cutoff = self.config.execution.cutoff_time
        return cutoff is None or timestamp.time() <= cutoff

    def _enter(
        self, candle: Candle, brick: Brick, direction: int, reason: str
    ) -> None:
        if self.position_direction or not self._can_enter(candle.timestamp):
            self._record(
                candle.timestamp,
                "entry_rejected",
                direction=direction,
                reason="position/cutoff/daily-limit",
            )
            return
        self.position_direction = direction
        self.entries_today += 1
        self.signals.notify_entry(direction)
        self.risk.enter(direction, candle.close, float(brick.box_size))
        legs = synthetic_entry_intents(
            self.config,
            candle.timestamp,
            direction,
            candle.close,
            reason,
        )
        self.intents.extend(legs)
        self._record(
            candle.timestamp,
            "entry",
            direction=direction,
            futures_price=candle.close,
            strike=legs[0].strike,
            expiry=self.config.execution.expiry,
            lots=self.config.execution.lots,
            reason=reason,
            active_stop=self.risk.active_level,
        )

    def _exit(self, timestamp: datetime, reason: str) -> None:
        if not self.position_direction:
            return
        direction = self.position_direction
        self.intents.append(
            SyntheticExitIntent(timestamp, self.config.underlying, direction, reason)
        )
        self._record(timestamp, "exit", direction=direction, reason=reason)
        self.position_direction = 0
        self.risk.clear()

    def _new_day(self, day: date) -> None:
        if self.current_day != day:
            self.current_day = day
            self.entries_today = 0

    def _record(self, timestamp: datetime, kind: str, **details: Any) -> None:
        self.events.append(EngineEvent(timestamp, kind, details))

    @staticmethod
    def _brick_dict(brick: Brick) -> dict[str, Any]:
        return {
            "sequence": brick.sequence,
            "open": float(brick.open),
            "close": float(brick.close),
            "direction": brick.direction,
            "box_size": float(brick.box_size),
        }
