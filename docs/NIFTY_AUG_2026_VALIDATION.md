# NIFTY 30-Minute Renko SPH/SPL Validation - August 2026

## Test Contract

- Signal chart: front-month NIFTY futures, completed 30-minute candles.
- Renko input: completed source-candle close.
- Renko reversal requirement: two boxes.
- Pivot confirmation: three consecutive bearish bricks confirm SPH; three consecutive bullish bricks confirm SPL.
- Pivots alternate and each confirmed pivot may trigger only once.
- Long/reverse long: completed brick closes above unused SPH.
- Short/reverse short: completed brick closes below unused SPL.
- Initial futures-price stop: 0.5% from signal fill.
- Execution: two lots of monthly synthetic futures.
- EMA and trailing stops: disabled.
- Warm-up: runs start 1 July 2026; this report filters pivot and entry events to August.
- Volrix data ends 14 August 2026.

## August Pivot Ledger

### ATR14, 1.0x

| Confirmation | Pivot | Level | Active box |
|---|---:|---:|---:|
| 04-Aug 12:44:59 | SPH | 24,674.35 | 40.20 |
| 05-Aug 09:44:59 | SPL | 24,517.70 | 39.40 |
| 11-Aug 09:44:59 | SPH | 24,727.95 | 36.55 |

### 0.05% of lagged LTP

| Confirmation | Pivot | Level | Active box |
|---|---:|---:|---:|
| 03-Aug 13:14:59 | SPH | 24,670.65 | 12.35 |
| 04-Aug 09:44:59 | SPL | 24,633.60 | 12.30 |
| 04-Aug 11:44:59 | SPH | 24,670.50 | 12.35 |
| 04-Aug 15:14:59 | SPL | 24,510.55 | 12.25 |
| 05-Aug 12:14:59 | SPH | 24,707.20 | 12.35 |
| 05-Aug 15:14:59 | SPL | 24,571.50 | 12.30 |
| 07-Aug 10:14:59 | SPH | 24,731.75 | 12.35 |
| 07-Aug 15:14:59 | SPL | 24,608.40 | 12.30 |
| 10-Aug 09:44:59 | SPH | 24,645.30 | 12.35 |
| 10-Aug 10:44:59 | SPL | 24,608.25 | 12.30 |
| 11-Aug 09:44:59 | SPH | 24,682.15 | 12.35 |
| 12-Aug 14:44:59 | SPL | 24,375.10 | 12.20 |
| 13-Aug 09:44:59 | SPH | 24,460.50 | 12.25 |
| 13-Aug 12:14:59 | SPL | 24,399.35 | 12.20 |
| 14-Aug 09:44:59 | SPH | 24,484.80 | 12.25 |
| 14-Aug 13:44:59 | SPL | 24,386.90 | 12.20 |

### Fixed 15 points

| Confirmation | Pivot | Level | Active box |
|---|---:|---:|---:|
| 03-Aug 13:14:59 | SPH | 24,679.60 | 15.00 |
| 05-Aug 09:44:59 | SPL | 24,514.60 | 15.00 |
| 05-Aug 12:14:59 | SPH | 24,709.60 | 15.00 |
| 05-Aug 15:14:59 | SPL | 24,574.60 | 15.00 |
| 07-Aug 10:14:59 | SPH | 24,739.60 | 15.00 |
| 10-Aug 10:44:59 | SPL | 24,604.60 | 15.00 |
| 11-Aug 09:44:59 | SPH | 24,679.60 | 15.00 |
| 12-Aug 14:44:59 | SPL | 24,379.60 | 15.00 |
| 13-Aug 11:14:59 | SPH | 24,454.60 | 15.00 |
| 13-Aug 12:14:59 | SPL | 24,409.60 | 15.00 |
| 14-Aug 09:44:59 | SPH | 24,484.60 | 15.00 |
| 14-Aug 13:44:59 | SPL | 24,379.60 | 15.00 |

## August Trade Summary

Gross points and rupees below include positions entered in August. Costs and slippage are not deducted.

| Box method | Positions | Gross points | Gross P&L | Observation |
|---|---:|---:|---:|---|
| ATR14 1.0x | 2 | -137.85 | -Rs 17,920.50 | Widest boxes and fewest signals |
| LTP 0.05% | 8 | -632.35 | -Rs 82,205.50 | Excessive churn in this sample |
| Fixed 15 | 3 | -113.55 | -Rs 14,761.50 | Least-negative August result |

The sample is too short to select a production configuration. All three are negative for August entries, and fixed 15 also has substantial July-August drawdown despite the smaller August loss.

## Sample Trigger Checks

| Method | Entry | Direction | Pivot trigger | Futures signal | 0.5% stop | Exit |
|---|---|---|---:|---:|---:|---|
| ATR14 | 05-Aug 09:45 | Long | SPH 24,674.35 | 24,710.00 | 24,586.45 | Stop, 05-Aug 13:00:59 |
| ATR14 | 12-Aug 10:15 | Short | SPL 24,517.70 | 24,437.10 | 24,559.29 | Open through test end |
| LTP 0.05% | 04-Aug 11:45 | Short | SPL 24,633.60 | 24,615.00 | 24,738.08 | Reverse, 05-Aug 09:44:59 |
| Fixed 15 | 11-Aug 09:45 | Short | SPL 24,604.60 | 24,538.30 | 24,660.99 | Reverse, 13-Aug 12:14:59 |
| Fixed 15 | 13-Aug 12:15 | Long | SPH 24,454.60 | 24,482.00 | 24,359.59 | Reverse, 14-Aug 11:14:59 |

The Volrix point timestamp is the final minute of the completed candle (for example `09:44:59`); the corresponding option trade is recorded at `09:45:00`.

## Volrix Runs

| Method | Trading report | Pivot analysis run |
|---|---|---|
| ATR14 | [Report](https://app.volrix.ai/report/d5ad3155-3ebe-4f1b-afc9-9033ca74b065?account=1ec2e10cddd2294622a3bb85b04c60486418cc28c1cf6bc4c2fe4ac24bff8799) | `97d29dcb-4489-42f9-aa4d-77ab4557a4c1` |
| LTP 0.05% | [Report](https://app.volrix.ai/report/e22c8777-d97a-4ffd-a5cc-799de10f86f5?account=df6aac0ccb1c8bf57a979775c8b9d5be3443f441de87ac64828f1b9f959e6233) | `d7f3a9cf-34ca-465f-b24e-71262997cf48` |
| Fixed 15 | [Report](https://app.volrix.ai/report/a64aa4d5-9fe0-4b06-a09c-6aa79fc54bbf?account=16291f319781348e69b1cd791cb8c8c797c68afd14da3aaad2ed4fbe0649f7b1) | `251ea967-e920-4dfd-aaba-b9a460cedcd7` |

## Implementation Finding

The first run allowed a stopped position to re-enter from the same previously consumed pivot. The signal state now versions each SPH/SPL and allows one breakout per confirmed pivot. The tables and run IDs above are from the corrected implementation.
