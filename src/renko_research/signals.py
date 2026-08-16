"""Renko reversal and pullback-continuation signal policies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bricks import Brick
from .config import SignalConfig
from .indicators import RecursiveEMA


class SignalAction(str, Enum):
    NONE = "none"
    ENTER_LONG = "enter_long"
    ENTER_SHORT = "enter_short"
    REVERSE_LONG = "reverse_long"
    REVERSE_SHORT = "reverse_short"
    EXIT = "exit"


@dataclass(frozen=True, slots=True)
class SignalDecision:
    action: SignalAction
    direction: int = 0
    reason: str = ""
    ema_value: float | None = None
    brick_close: float | None = None


@dataclass(frozen=True, slots=True)
class PivotEvent:
    kind: str
    price: float
    brick_sequence: int


class SignalEngine:
    def __init__(self, config: SignalConfig) -> None:
        self.config = config
        self.ema = RecursiveEMA(config.ema_period) if config.ema_period else None
        self.brick_direction = 0
        self.last_traded_direction = 0
        self.continuation_anchor = 0
        self.counter_boxes = 0
        self.ema_wait_direction = 0
        self.sph: float | None = None
        self.spl: float | None = None
        self.can_mark_sph = True
        self.can_mark_spl = False
        self.highest_since_pivot: tuple[float, int] | None = None
        self.lowest_since_pivot: tuple[float, int] | None = None
        self.same_direction_count = 0
        self.last_pivots: list[PivotEvent] = []
        self.sph_version = 0
        self.spl_version = 0
        self.used_sph_version = 0
        self.used_spl_version = 0

    def notify_entry(self, direction: int) -> None:
        self.last_traded_direction = direction
        if self.config.continuation_anchor == "last_traded_trend":
            self.continuation_anchor = direction

    def _eligible(self, direction: int, brick: Brick) -> tuple[bool, float | None]:
        if self.ema is None:
            return True, None
        value = float(self.ema.value) if self.ema.value is not None else None
        if not self.ema.ready or value is None:
            return False, value
        eligible = float(brick.close) > value if direction > 0 else float(brick.close) < value
        return eligible, value

    @staticmethod
    def _entry_action(direction: int, reverse: bool) -> SignalAction:
        if reverse:
            return SignalAction.REVERSE_LONG if direction > 0 else SignalAction.REVERSE_SHORT
        return SignalAction.ENTER_LONG if direction > 0 else SignalAction.ENTER_SHORT

    def process(
        self, bricks: list[Brick], *, position_direction: int = 0
    ) -> SignalDecision:
        if not bricks:
            return SignalDecision(SignalAction.NONE)

        if self.config.mode == "sph_spl":
            return self._process_sph_spl(bricks, position_direction)

        previous_direction = self.brick_direction
        continuation_candidate = 0
        for brick in bricks:
            if self.ema is not None:
                self.ema.update(brick.close)
            direction = brick.direction
            if self.config.mode == "pullback_continuation":
                anchor = self._anchor_for(brick)
                if anchor:
                    if direction == anchor:
                        if (
                            self.config.pullback_min_boxes
                            <= self.counter_boxes
                            <= self.config.pullback_max_boxes
                        ):
                            continuation_candidate = anchor
                        self.counter_boxes = 0
                    else:
                        self.counter_boxes += 1
            self.brick_direction = direction

        final = bricks[-1]
        direction = final.direction
        eligible, ema_value = self._eligible(direction, final)
        flipped = previous_direction != 0 and direction != previous_direction

        if position_direction and direction == -position_direction and flipped:
            self.ema_wait_direction = 0 if eligible else direction
            if eligible:
                return SignalDecision(
                    self._entry_action(direction, reverse=True),
                    direction,
                    "qualified Renko reversal",
                    ema_value,
                    float(final.close),
                )
            return SignalDecision(
                SignalAction.EXIT,
                0,
                "EMA-rejected reversal exit-only",
                ema_value,
                float(final.close),
            )

        if position_direction:
            return SignalDecision(SignalAction.NONE, ema_value=ema_value)

        if self.config.mode == "pullback_continuation" and continuation_candidate:
            candidate_ok, ema_value = self._eligible(continuation_candidate, final)
            if candidate_ok:
                return SignalDecision(
                    self._entry_action(continuation_candidate, reverse=False),
                    continuation_candidate,
                    "confirmed pullback resumption",
                    ema_value,
                    float(final.close),
                )

        initial_or_flip = previous_direction == 0 or flipped
        if self.config.mode == "reversal" and initial_or_flip:
            if eligible:
                self.ema_wait_direction = 0
                return SignalDecision(
                    self._entry_action(direction, reverse=False),
                    direction,
                    "initial Renko trend" if previous_direction == 0 else "Renko reversal",
                    ema_value,
                    float(final.close),
                )
            self.ema_wait_direction = direction

        if self.ema_wait_direction == direction and eligible:
            self.ema_wait_direction = 0
            return SignalDecision(
                self._entry_action(direction, reverse=False),
                direction,
                "delayed EMA alignment",
                ema_value,
                float(final.close),
            )

        return SignalDecision(
            SignalAction.NONE,
            ema_value=ema_value,
            brick_close=float(final.close),
        )

    def _process_sph_spl(
        self, bricks: list[Brick], position_direction: int
    ) -> SignalDecision:
        self.last_pivots = []
        breakout = 0
        breakout_level: float | None = None
        previous_brick_direction = self.brick_direction

        for brick in bricks:
            if self.ema is not None:
                self.ema.update(brick.close)
            high = float(brick.high)
            low = float(brick.low)
            if self.highest_since_pivot is None or high > self.highest_since_pivot[0]:
                self.highest_since_pivot = (high, brick.sequence)
            if self.lowest_since_pivot is None or low < self.lowest_since_pivot[0]:
                self.lowest_since_pivot = (low, brick.sequence)

            if brick.direction == previous_brick_direction:
                self.same_direction_count += 1
            else:
                self.same_direction_count = 1
            previous_brick_direction = brick.direction

            if (
                self.sph is not None
                and self.sph_version > self.used_sph_version
                and float(brick.close) > self.sph
            ):
                breakout = 1
                breakout_level = self.sph
                self.used_sph_version = self.sph_version
            elif (
                self.spl is not None
                and self.spl_version > self.used_spl_version
                and float(brick.close) < self.spl
            ):
                breakout = -1
                breakout_level = self.spl
                self.used_spl_version = self.spl_version

            required = self.config.pivot_confirmation_boxes
            if brick.direction < 0 and self.can_mark_sph and self.same_direction_count >= required:
                assert self.highest_since_pivot is not None
                self.sph = self.highest_since_pivot[0]
                self.sph_version += 1
                self.last_pivots.append(
                    PivotEvent("SPH", self.sph, self.highest_since_pivot[1])
                )
                self.can_mark_sph = False
                self.can_mark_spl = True
                self.highest_since_pivot = (high, brick.sequence)
                self.lowest_since_pivot = (low, brick.sequence)
            elif brick.direction > 0 and self.can_mark_spl and self.same_direction_count >= required:
                assert self.lowest_since_pivot is not None
                self.spl = self.lowest_since_pivot[0]
                self.spl_version += 1
                self.last_pivots.append(
                    PivotEvent("SPL", self.spl, self.lowest_since_pivot[1])
                )
                self.can_mark_spl = False
                self.can_mark_sph = True
                self.highest_since_pivot = (high, brick.sequence)
                self.lowest_since_pivot = (low, brick.sequence)

            self.brick_direction = brick.direction

        final = bricks[-1]
        ema_value = float(self.ema.value) if self.ema and self.ema.value is not None else None
        if breakout == 0 or breakout == position_direction:
            return SignalDecision(
                SignalAction.NONE,
                ema_value=ema_value,
                brick_close=float(final.close),
            )

        eligible, ema_value = self._eligible(breakout, final)
        level_name = "SPH" if breakout > 0 else "SPL"
        reason = f"{level_name} breakout level={breakout_level:.2f}"
        if not eligible:
            if position_direction:
                return SignalDecision(
                    SignalAction.EXIT,
                    0,
                    f"EMA-rejected {reason}",
                    ema_value,
                    float(final.close),
                )
            return SignalDecision(
                SignalAction.NONE,
                ema_value=ema_value,
                brick_close=float(final.close),
            )
        return SignalDecision(
            self._entry_action(breakout, reverse=position_direction != 0),
            breakout,
            reason,
            ema_value,
            float(final.close),
        )

    def _anchor_for(self, brick: Brick) -> int:
        if self.config.continuation_anchor == "last_traded_trend":
            if self.continuation_anchor == 0:
                self.continuation_anchor = self.last_traded_direction or brick.direction
            return self.continuation_anchor
        if self.ema is None or not self.ema.ready or self.ema.value is None:
            return 0
        regime = 1 if brick.close > self.ema.value else -1 if brick.close < self.ema.value else 0
        if regime and regime != self.continuation_anchor:
            self.continuation_anchor = regime
            self.counter_boxes = 0
        return self.continuation_anchor
