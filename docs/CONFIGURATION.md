# Configuration Reference

The YAML configuration is validated before local execution or Volrix code
generation. See `configs/nifty.yaml` and `configs/banknifty.yaml` for complete
examples.

## Source and Renko

- `source.timeframe_minutes`: one of `1, 2, 3, 5, 10, 15, 20, 25, 30, 45, 60, 120, 240`.
- `renko.box_mode`: `fixed_points`, `ltp_percent`, `atr`, or `annual_percent`.
- `fixed_points`: constant futures points per box.
- `ltp_percent`: percentage of the previous completed source close.
- `atr`: prior completed Wilder ATR times `atr_multiplier`.
- `annual_percent`: percentage of the prior calendar year's final active
  front-month futures close, frozen for the next calendar year.
- `reversal_boxes`: minimum full-box counter move required before reversal
  bricks are emitted.

ATR and LTP modes always use a one-source-bar lag. A source bar may create
multiple bricks, but all of them use the same size and result in at most one
trading decision.

## Signal and Risk

- `signal.ema_period: null` disables EMA. Otherwise EMA is recursively updated
  from each completed Renko close and trades begin only after warm-up.
- `reversal` enters on a qualified direction change.
- `pullback_continuation` enters when the configured countertrend run returns
  to either the last traded direction or the active EMA regime.
- Initial stop types are `entry_percent` and `box_offset`.
- Trailing types are `atr_from_brick`, `opposite_boxes`, and
  `price_box_offset`.
- All enabled stops coexist. The tightest active futures-price level wins and
  no trailing level may loosen.

## Execution

- Signals and stops always use front-month futures.
- Long synthetic: buy ATM CE and sell ATM PE.
- Short synthetic: sell ATM CE and buy ATM PE.
- `lots` uses Volrix historical lot-size resolution.
- NIFTY accepts `weekly` or `monthly`; BANKNIFTY accepts `monthly` only.
- `holding` accepts `intraday` or `positional`.
- Null `max_entries_per_day` and `entry_cutoff` mean unlimited/no cutoff.
- Intraday positions close at `intraday_exit`; chart state remains positional.

Current and next futures charts are warmed independently. A monthly futures
roll promotes the warmed next chart, preserves direction, and rebases active
underlying risk to the new futures reference.
