"""Deterministic close-based Renko construction without look-ahead."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Brick:
    timestamp: datetime
    open: Decimal
    close: Decimal
    direction: int
    sequence: int
    box_size: Decimal

    @property
    def high(self) -> Decimal:
        return max(self.open, self.close)

    @property
    def low(self) -> Decimal:
        return min(self.open, self.close)


class RenkoBuilder:
    """Build close-based bricks from completed source candles.

    A reversal requires ``reversal_bricks`` full boxes from the latest brick
    close. Once confirmed, every complete box in the move is emitted. This
    explicit convention avoids provider-specific intrabar assumptions.
    """

    def __init__(
        self,
        brick_size: Decimal | str | float,
        *,
        initial_price: Decimal | str | float | None = None,
        reversal_bricks: int = 1,
    ) -> None:
        self.brick_size = Decimal(str(brick_size))
        if self.brick_size <= 0:
            raise ValueError("brick_size must be positive")
        if reversal_bricks < 1:
            raise ValueError("reversal_bricks must be at least one")
        self.reversal_bricks = reversal_bricks
        self.last_close = (
            Decimal(str(initial_price)) if initial_price is not None else None
        )
        self.direction = 0
        self.sequence = 0

    def update(
        self,
        timestamp: datetime,
        completed_close: Decimal | str | float,
        *,
        brick_size: Decimal | str | float | None = None,
    ) -> list[Brick]:
        price = Decimal(str(completed_close))
        active_size = (
            self.brick_size if brick_size is None else Decimal(str(brick_size))
        )
        if active_size <= 0:
            raise ValueError("brick_size must be positive")
        if self.last_close is None:
            self.last_close = price
            return []

        move = price - self.last_close
        candidate_direction = 1 if move > 0 else -1 if move < 0 else 0
        if candidate_direction == 0:
            return []

        threshold = active_size
        if self.direction and candidate_direction != self.direction:
            threshold *= self.reversal_bricks
        if abs(move) < threshold:
            return []

        brick_count = int(abs(move) // active_size)
        bricks: list[Brick] = []
        for _ in range(brick_count):
            brick_open = self.last_close
            brick_close = brick_open + candidate_direction * active_size
            self.sequence += 1
            brick = Brick(
                timestamp=timestamp,
                open=brick_open,
                close=brick_close,
                direction=candidate_direction,
                sequence=self.sequence,
                box_size=active_size,
            )
            bricks.append(brick)
            self.last_close = brick_close
        self.direction = candidate_direction
        return bricks

    def build(
        self,
        closes: Iterable[tuple[datetime, Decimal | str | float]],
    ) -> list[Brick]:
        bricks: list[Brick] = []
        for timestamp, close in closes:
            bricks.extend(self.update(timestamp, close))
        return bricks
