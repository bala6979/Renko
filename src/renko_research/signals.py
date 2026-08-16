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


class SignalEngine:
    def __init__(self, config: SignalConfig) -> None:
        self.config = config
        self.ema = RecursiveEMA(config.ema_period) if config.ema_period else None
        self.brick_direction = 0
        self.last_traded_direction = 0
        self.continuation_anchor = 0
        self.counter_boxes = 0
        self.ema_wait_direction = 0

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
