# Locked Baseline Snapshot

These values are copied from the locked strategy reports in
`KiteTradingAutomation`. They are benchmark snapshots, not recomputed results.
Every Renko comparison must use the same date range and cost model before a
conclusion is made.

| System | Period | Net points | Net P&L | PF | Reward-risk | MDD points | Sharpe | Sortino | Calmar |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NIFTY 30m corrected SPH/SPL | 2019-02-11 to 2026-08-14 | 15,249.70 | Rs 1,982,460.95 | 1.24 | 2.40 | -2,492.81 | 0.88 | 1.35 | 0.40 |
| BANKNIFTY 30m corrected HA3C EMA50 | 2021-01-01 to 2026-08-14 | 38,211.23 | Rs 2,292,673.90 | 1.35 | 2.44 | -4,329.83 | 1.11 | 2.01 | 0.75 |
| NIFTY 5m HA5C EMA200 STBT | Report snapshot | 16,750.83 | Rs 2,177,571.08 | 1.63 | 1.32 | -666.21 | 2.67 | 3.45 | 1.57 |
| BANKNIFTY 5m ST10,3 EMA200, individual 30% leg SL | Report snapshot | 34,791.60 | Rs 2,087,497.00 | 1.63 | 1.95 | N/A | 1.96 | N/A | 1.87 |

Before automated ranking, import the authoritative ledgers and regenerate these
metrics with one shared reporting implementation.

