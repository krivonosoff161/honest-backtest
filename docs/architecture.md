# The validation architecture

```
   a backtest result you want to believe
                  │
   ┌──────────────▼──────────────┐
   │ 1. data integrity           │  look-ahead? survivorship? ordered bars?
   ├─────────────────────────────┤
   │ 2. validation splits        │  holdout · walk-forward · purged k-fold
   ├─────────────────────────────┤
   │ 3. significance             │  bootstrap CI · permutation · multiple-testing
   ├─────────────────────────────┤
   │ 4. costs                    │  gross vs net (fees + slippage)
   ├─────────────────────────────┤
   │ 5. robustness               │  param plateau? sub-period stability?
   ├─────────────────────────────┤
   │ 6. forward                  │  out-of-time / paper — the only real test
   ├─────────────────────────────┤
   │ 7. AI adversarial review    │  a panel tries to REFUTE it
   └──────────────┬──────────────┘
                  │
       "not obviously broken"  (≠ true)
```

Each layer removes one class of self-deception:

1. **Data integrity** — the cheapest lies. A feature that uses information it wouldn't have had at decision time will look brilliant. A universe of only-survivors hides every failure.
2. **Validation splits** — you may never judge a strategy on the data you tuned it on. Walk-forward is the honest default for time series; purged k-fold adds a gap so neighbours can't leak.
3. **Significance** — a positive mean is not an edge until it's distinguishable from luck. Bootstrap the CI; permute to build the null; if you tried many things, correct for it.
4. **Costs** — gross returns are fiction. Subtract fees and slippage; if net ≤ 0, there is no edge to trade.
5. **Robustness** — a real edge is a plateau across parameters and sub-periods, not a single lucky spike.
6. **Forward** — everything above only proves "not obviously broken". The one honest test is performance on data you had not seen when you decided.
7. **AI adversarial review** — one model pass rationalizes; an adversarial panel, each with a different skeptical lens, refutes. Majority-refute → drop the finding.

## The meta-caveat

The pipeline above is itself a set of choices — which layers, which thresholds, which order, what counts as passing. **Run enough validation variants and one passes by chance.** Treat this architecture as discipline, not as an oracle of truth. The honest output is never "this works"; it is "this is not yet falsified — now run it forward."
