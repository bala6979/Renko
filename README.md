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

## Configuration and Volrix generation

Complete example configurations are in `configs/`. Generate a standalone
Volrix class with:

```powershell
python scripts/generate_volrix.py configs/nifty.yaml strategies/volrix/generated_nifty.py --class-name NiftyRenkoSample
```

The generated artifact contains no imports or local module references. Futures
prices drive signals and risk; the tradable legs are an ATM synthetic future.
NIFTY supports weekly or monthly options and BANKNIFTY is validated as monthly
only.

Detailed field behavior is in
[docs/CONFIGURATION.md](docs/CONFIGURATION.md). The initial runtime evidence is
recorded in [docs/VOLRIX_SAMPLE_VALIDATION.md](docs/VOLRIX_SAMPLE_VALIDATION.md).
