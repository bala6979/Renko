# Volrix Sample Validation

Validation date: 2026-08-16. These are integration samples, not strategy
recommendations or full-history performance results.

## NIFTY ATR EMA50

- Run: `696b0c0d-a7bc-4702-9e15-7efc78903dec`
- Period: 2026-07-20 through 2026-08-05.
- Generated class passed Volrix diagnostics and completed.
- 26 option-leg trades, representing 13 two-leg synthetic positions.
- Sample short signal: futures `23,760`, box `21.20`, EMA `23,958.28`.
- Execution: sell `23,750 CE`, buy `23,750 PE`, two historical lots,
  quantity `130` per leg.

## BANKNIFTY Annual Warm-up

- Run: `6f4c9f54-5a94-4d40-8c46-9bbf90737336`
- Period: 2025-12-01 through 2026-01-15.
- The annual-percent continuation configuration completed without trades. This
  verifies the skip/warm-up path but is intentionally not used as fill parity.

## BANKNIFTY Fixed-Box Fill Parity

- Run: `c959831f-d9bb-4b24-98f6-1891f627b321`
- Period: 2026-07-20 through 2026-08-05.
- Generated class passed Volrix diagnostics and completed.
- 20 option-leg trades, representing 10 two-leg synthetic positions.
- Sample short signal: futures `57,941`, box `100`, EMA `58,004.86`.
- Execution: sell `57,900 CE`, buy `57,900 PE`, two historical lots,
  quantity `60` per leg.

The sample runs use zero configured slippage. Their short periods and Volrix
headline P&L are not evidence that a parameter set beats a locked baseline.
