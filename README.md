# Renko Strategy Research

Independent research repository for testing Renko-based NIFTY and BANKNIFTY
strategies against the locked systems in `KiteTradingAutomation`.

## Research principles

- Build bricks only from completed one-minute candles.
- Never use future candles to choose a brick size.
- Separate the signal instrument from the execution instrument.
- Apply historical contract selection, lot sizes, and order-level costs.
- Use walk-forward and recent-period checks before promoting a strategy.
- Compare risk-adjusted returns, not only net profit.

## Initial scope

- Underlyings: NIFTY and BANKNIFTY.
- Brick sizing: fixed percentage and prior-session ATR multiples.
- Signal modes: continuation, reversal, and trend-filtered variants.
- Execution candidates: futures, monthly synthetic futures, and directional
  option buying or selling where appropriate.
- Outputs: gross/net points, rupee P&L, costs, drawdown, profit factor,
  expectancy, reward-risk, Sharpe, Sortino, Calmar, and year-month matrices.

See [docs/RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md) for the promotion
rules and [docs/LOCKED_BASELINES.md](docs/LOCKED_BASELINES.md) for the benchmark
snapshot.

## Setup

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```

The core builder is intentionally provider-independent. Volrix-compatible
strategy implementations belong under `strategies/volrix/` and must reproduce
the local brick stream on sampled dates before full-history runs are accepted.

