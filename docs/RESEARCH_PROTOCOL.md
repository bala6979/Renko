# Research Protocol

## Data and brick construction

1. Consume completed one-minute normal candles in exchange order.
2. Build close-based bricks; never infer the high-low path inside a minute.
3. For percentage bricks, freeze the size from a prior completed reference.
4. For ATR bricks, use ATR known before the trading session starts.
5. Preserve brick state overnight unless a tested strategy explicitly resets it.
6. Record source timestamp, brick sequence, size, and every signal decision.

## Experiment sequence

1. Reconcile local bricks with Volrix on sampled trending, reversal, gap, and
   multi-brick minutes.
2. Sweep brick size on the signal instrument with execution disabled.
3. Freeze viable signal parameters using walk-forward validation.
4. Test execution instruments and costs only after signal selection.
5. Run the selected strategy over full history and `2024-latest` separately.
6. Compare it with the locked benchmark over identical dates.

## Promotion criteria

A Renko candidate is not promoted merely for higher profit. It must:

- Produce positive net results over full history and `2024-latest`.
- Have adequate trade count across multiple market regimes.
- Match or improve the corresponding baseline profit factor and Calmar ratio.
- Avoid materially worse percentage drawdown unless return improvement clearly
  compensates for it.
- Remain profitable after the established order-level charges and a documented
  slippage sensitivity.
- Avoid dependence on one year, weekday, direction, or expiry regime.
- Pass a final untouched out-of-sample or anchored walk-forward period.

All parameter sweeps remain research candidates until these checks pass.

