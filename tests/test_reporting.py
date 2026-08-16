from datetime import datetime, timedelta

from renko_research.reporting import ClosedTrade, maximum_drawdown, summarize


def test_reporting_includes_points_risk_and_month_matrix() -> None:
    start = datetime(2026, 1, 2, 10)
    trades = [
        ClosedTrade(start, start + timedelta(hours=1), 1, 10, 100, 1000, 100),
        ClosedTrade(
            start + timedelta(days=1),
            start + timedelta(days=1, hours=1),
            -1,
            -5,
            100,
            -500,
            100,
        ),
    ]
    result = summarize(trades, reporting_capital=600_000)
    assert result["gross_points"] == 5
    assert result["net_points"] == 3
    assert result["net_pnl"] == 300
    assert result["reward_risk"] == 1.5
    assert result["monthly_net_points"] == {"2026-01": 3}


def test_maximum_drawdown_uses_realized_equity() -> None:
    assert maximum_drawdown([100, -40, -80, 30]) == -120
