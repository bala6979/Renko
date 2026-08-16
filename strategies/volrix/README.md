# Volrix Implementations

Volrix strategy classes will be added here after local brick construction is
validated. Each class must embed the complete Renko logic because Volrix cannot
read this repository's local runtime during a remote backtest.

Run validation before consuming full-history backtests. Compare sampled brick
timestamps and levels with `renko_research.RenkoBuilder`, then run candidates
sequentially or within the currently verified Volrix concurrency entitlement.

