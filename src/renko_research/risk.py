"""Underlying-futures risk controls for synthetic execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from .bricks import Brick
from .config import RiskConfig


@dataclass(frozen=True, slots=True)
class StopHit:
    level: float
    reason: str


@dataclass(slots=True)
class RiskManager:
    config: RiskConfig
    direction: int = 0
    entry_price: float | None = None
    entry_box_size: float | None = None
    best_price: float | None = None
    latest_favorable_brick: float | None = None
    initial_levels: dict[str, float] = field(default_factory=dict)
    trailing_levels: dict[str, float] = field(default_factory=dict)
    opposite_box_count: int = 0

    def enter(self, direction: int, entry_price: float, box_size: float) -> None:
        self.clear()
        self.direction = direction
        self.entry_price = entry_price
        self.entry_box_size = box_size
        self.best_price = entry_price
        self.latest_favorable_brick = entry_price
        for stop in self.config.initial_stops:
            if stop.type == "entry_percent":
                distance = entry_price * float(stop.value) / 100.0
            else:
                distance = box_size * float(stop.value)
            self.initial_levels[stop.type] = entry_price - direction * distance

    def clear(self) -> None:
        self.direction = 0
        self.entry_price = None
        self.entry_box_size = None
        self.best_price = None
        self.latest_favorable_brick = None
        self.initial_levels.clear()
        self.trailing_levels.clear()
        self.opposite_box_count = 0

    @property
    def active_level(self) -> float | None:
        levels = [*self.initial_levels.values(), *self.trailing_levels.values()]
        if not levels or not self.direction:
            return None
        return max(levels) if self.direction > 0 else min(levels)

    def check_price_bar(self, high: float, low: float) -> StopHit | None:
        level = self.active_level
        if level is not None:
            hit = low <= level if self.direction > 0 else high >= level
            if hit:
                return StopHit(level, "underlying price stop")

        if self.direction > 0:
            self.best_price = max(float(self.best_price), high)
        elif self.direction < 0:
            self.best_price = min(float(self.best_price), low)
        return None

    def update_price_box_trails(self, box_size: float) -> None:
        if not self.direction or self.best_price is None:
            return
        for stop in self.config.trailing_stops:
            if stop.type != "price_box_offset":
                continue
            candidate = self.best_price - self.direction * box_size * int(stop.boxes)
            self._ratchet("price_box_offset", candidate)

    def process_bricks(
        self, bricks: list[Brick], *, atr_value: float | None
    ) -> StopHit | None:
        if not self.direction:
            return None
        for brick in bricks:
            if brick.direction == self.direction:
                self.opposite_box_count = 0
                self.latest_favorable_brick = float(brick.close)
                for stop in self.config.trailing_stops:
                    if stop.type == "atr_from_brick" and atr_value is not None:
                        candidate = float(brick.close) - self.direction * float(
                            stop.multiplier
                        ) * atr_value
                        self._ratchet("atr_from_brick", candidate)
            else:
                self.opposite_box_count += 1

        for stop in self.config.trailing_stops:
            if (
                stop.type == "opposite_boxes"
                and self.opposite_box_count >= int(stop.boxes)
            ):
                return StopHit(float(bricks[-1].close), "completed opposite-box TSL")
        return None

    def _ratchet(self, name: str, candidate: float) -> None:
        existing = self.trailing_levels.get(name)
        if existing is None:
            self.trailing_levels[name] = candidate
        elif self.direction > 0:
            self.trailing_levels[name] = max(existing, candidate)
        else:
            self.trailing_levels[name] = min(existing, candidate)

    def rebase(self, futures_price: float, box_size: float) -> None:
        if not self.direction:
            return
        direction = self.direction
        self.enter(direction, futures_price, box_size)
