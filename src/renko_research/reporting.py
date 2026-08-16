"""Trade metrics used to compare Renko candidates with locked baselines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt


@dataclass(frozen=True, slots=True)
class ClosedTrade:
    entry_time: datetime
    exit_time: datetime
    direction: int
    gross_points: float
    quantity: int
    gross_pnl: float
    charges: float

    @property
    def net_points(self) -> float:
        return self.gross_points - self.charges / self.quantity

    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.charges


def summarize(trades: list[ClosedTrade], reporting_capital: float) -> dict[str, object]:
    pnl = [item.net_pnl for item in trades]
    points = [item.net_points for item in trades]
    wins = [value for value in pnl if value > 0]
    losses = [value for value in pnl if value < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    average_win = gross_profit / len(wins) if wins else 0.0
    average_loss = gross_loss / len(losses) if losses else 0.0
    reward_risk = average_win / average_loss if average_loss else float("inf")
    profit_factor = gross_profit / gross_loss if gross_loss else float("inf")
    expectancy = sum(pnl) / len(pnl) if pnl else 0.0
    mdd = maximum_drawdown(pnl)
    daily: dict[object, float] = {}
    monthly: dict[str, float] = {}
    for trade in trades:
        day = trade.exit_time.date()
        daily[day] = daily.get(day, 0.0) + trade.net_pnl
        month = trade.exit_time.strftime("%Y-%m")
        monthly[month] = monthly.get(month, 0.0) + trade.net_points
    returns = [value / reporting_capital for value in daily.values()]
    sharpe = annualized_ratio(returns, downside_only=False)
    sortino = annualized_ratio(returns, downside_only=True)
    years = max(
        (trades[-1].exit_time - trades[0].entry_time).days / 365.25,
        1 / 365.25,
    ) if trades else 0.0
    ending = reporting_capital + sum(pnl)
    cagr = (ending / reporting_capital) ** (1 / years) - 1 if trades and ending > 0 else -1.0
    calmar = cagr / (abs(mdd) / reporting_capital) if mdd else float("inf")
    return {
        "trades": len(trades),
        "gross_points": sum(item.gross_points for item in trades),
        "net_points": sum(points),
        "gross_pnl": sum(item.gross_pnl for item in trades),
        "charges": sum(item.charges for item in trades),
        "net_pnl": sum(pnl),
        "win_rate": len(wins) / len(pnl) if pnl else 0.0,
        "average_win": average_win,
        "average_loss": average_loss,
        "reward_risk": reward_risk,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "mdd_pnl": mdd,
        "mdd_percent": abs(mdd) / reporting_capital,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "cagr": cagr,
        "monthly_net_points": monthly,
        "max_winning_streak": streak(pnl, positive=True),
        "max_losing_streak": streak(pnl, positive=False),
    }


def maximum_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return drawdown


def annualized_ratio(values: list[float], *, downside_only: bool) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    sample = [min(value, 0.0) for value in values] if downside_only else values
    variance = sum((value - (0.0 if downside_only else mean)) ** 2 for value in sample)
    variance /= len(sample) - 1
    deviation = sqrt(variance)
    return mean / deviation * sqrt(252) if deviation else 0.0


def streak(values: list[float], *, positive: bool) -> int:
    best = current = 0
    for value in values:
        match = value > 0 if positive else value < 0
        current = current + 1 if match else 0
        best = max(best, current)
    return best
