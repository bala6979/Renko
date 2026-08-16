"""Established Indian index-option order charges."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OptionChargeSchedule:
    brokerage_per_order: float = 20.0
    stt_sell_rate: float = 0.0015
    exchange_rate: float = 0.0005
    sebi_rate: float = 0.000001
    stamp_buy_rate: float = 0.00003
    gst_rate: float = 0.18


@dataclass(frozen=True, slots=True)
class OrderCharges:
    brokerage: float
    stt: float
    exchange: float
    sebi: float
    stamp: float
    gst: float

    @property
    def total(self) -> float:
        return self.brokerage + self.stt + self.exchange + self.sebi + self.stamp + self.gst


def option_order_charges(
    *,
    side: str,
    premium: float,
    quantity: int,
    schedule: OptionChargeSchedule = OptionChargeSchedule(),
) -> OrderCharges:
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
    if premium < 0 or quantity <= 0:
        raise ValueError("premium must be non-negative and quantity positive")
    turnover = premium * quantity
    brokerage = schedule.brokerage_per_order
    stt = turnover * schedule.stt_sell_rate if side == "sell" else 0.0
    exchange = turnover * schedule.exchange_rate
    sebi = turnover * schedule.sebi_rate
    stamp = turnover * schedule.stamp_buy_rate if side == "buy" else 0.0
    gst = (brokerage + exchange + sebi) * schedule.gst_rate
    return OrderCharges(brokerage, stt, exchange, sebi, stamp, gst)
