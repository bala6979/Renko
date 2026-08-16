"""Synthetic-futures execution mapping and audit records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .config import RenkoStrategyConfig


@dataclass(frozen=True, slots=True)
class SyntheticLegIntent:
    timestamp: datetime
    underlying: str
    direction: int
    option_type: str
    side: str
    strike: int
    expiry_type: str
    lots: int
    reason: str


@dataclass(frozen=True, slots=True)
class SyntheticExitIntent:
    timestamp: datetime
    underlying: str
    direction: int
    reason: str


def nearest_strike(underlying: str, futures_price: float) -> int:
    interval = 50 if underlying == "NIFTY" else 100
    return int(round(futures_price / interval) * interval)


def synthetic_entry_intents(
    config: RenkoStrategyConfig,
    timestamp: datetime,
    direction: int,
    futures_price: float,
    reason: str,
) -> tuple[SyntheticLegIntent, SyntheticLegIntent]:
    strike = nearest_strike(config.underlying, futures_price)
    if direction > 0:
        legs = (("CE", "buy"), ("PE", "sell"))
    else:
        legs = (("CE", "sell"), ("PE", "buy"))
    return tuple(
        SyntheticLegIntent(
            timestamp=timestamp,
            underlying=config.underlying,
            direction=direction,
            option_type=option_type,
            side=side,
            strike=strike,
            expiry_type=config.execution.expiry,
            lots=config.execution.lots,
            reason=reason,
        )
        for option_type, side in legs
    )  # type: ignore[return-value]
