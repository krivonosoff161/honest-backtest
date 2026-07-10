# Public API Reference

Status: **STABLE API** for `backtest_sanity` version `0.1.0`.

Only symbols exported by `backtest_sanity.__all__` are public compatibility
surface. Direct helpers from internal modules may change without notice.

## Input Convention

Functions accept Python lists or NumPy-compatible numeric arrays. Returns are
plain scalars, lists, tuples, or dictionaries. Inputs should be ordered in time
and must represent returns or observations already computed by the caller.

The toolkit does not fetch prices, calculate signals, place orders, or validate
private data quality beyond the explicit checks below.

| Layer | Exports | Result |
|---|---|---|
| Data integrity | `lookahead_correlation`, `timestamp_monotonic`, `survivorship_note` | Leakage/order diagnostic. |
| Splits | `holdout`, `walk_forward`, `purged_kfold` | Train/test index lists. `walk_forward` rejects non-positive sizes or steps. |
| Significance | `bootstrap_ci`, `permutation_test`, `bonferroni`, `benjamini_hochberg` | Confidence/p-value or correction result. Assumes i.i.d. observations. |
| Overfitting | `probabilistic_sharpe_ratio`, `deflated_sharpe_ratio`, `minimum_track_record_length`, `probability_of_backtest_overfitting` | Named overfitting statistics; assumptions remain caller responsibility. |
| Costs | `apply_costs` | Gross/net return arrays, means, cost drag, and `survives_costs`. |
| Robustness | `param_sweep`, `subperiod_stability` | Parameter-neighbourhood or subperiod stability summary. |
| Forward evidence | `ForwardLog` | Local JSONL decision/outcome record. |
| Adversarial review | `adversarial_review` | Aggregate result over caller-provided verifier functions. |

## Error Behaviour

- Invalid split dimensions raise `ValueError`.
- Statistical functions can return `NaN` or raise `ValueError` for degenerate
  input; callers must treat that as inconclusive, not positive evidence.
- No function converts an inconclusive result into a recommendation or order.

## ForwardLog Boundary

`ForwardLog.record()` appends a JSON object with `logged_at`; `rows()` reads it
back. It is inspectable local evidence, not a tamper-proof ledger: it does not
provide locking, hash chaining, signing, IDs, or write-once storage. Systems
that need stronger evidence must add those controls outside this small toolkit.

## Compatibility Rule

New public exports require tests, an example when they teach a distinct failure
mode, and updates to this document, `README.md`, and `docs/project-map.md`.
