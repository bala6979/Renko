"""Streaming indicators with explicit warm-up state."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class RecursiveEMA:
    period: int
    value: Decimal | None = None
    count: int = 0

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("EMA period must be positive")

    @property
    def ready(self) -> bool:
        return self.count >= self.period

    def update(self, price: Decimal | str | float) -> Decimal:
        current = Decimal(str(price))
        self.count += 1
        if self.value is None:
            self.value = current
        else:
            alpha = Decimal(2) / Decimal(self.period + 1)
            self.value = alpha * current + (Decimal(1) - alpha) * self.value
        return self.value
