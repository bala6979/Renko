"""Leakage-safe brick-size helpers."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def percentage_brick(reference_price: float, percentage: float, tick: float) -> Decimal:
    if reference_price <= 0 or percentage <= 0 or tick <= 0:
        raise ValueError("reference_price, percentage, and tick must be positive")
    raw = Decimal(str(reference_price)) * Decimal(str(percentage)) / Decimal("100")
    return _round_to_tick(raw, Decimal(str(tick)))


def prior_atr_brick(prior_session_atr: float, multiplier: float, tick: float) -> Decimal:
    """Use only an ATR finalized before the session being traded."""
    if prior_session_atr <= 0 or multiplier <= 0 or tick <= 0:
        raise ValueError("prior_session_atr, multiplier, and tick must be positive")
    raw = Decimal(str(prior_session_atr)) * Decimal(str(multiplier))
    return _round_to_tick(raw, Decimal(str(tick)))


def _round_to_tick(value: Decimal, tick: Decimal) -> Decimal:
    ticks = (value / tick).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return ticks * tick

