# Architecture

Status: **CURRENT**

- Verified: 2026-08-29
- Verified against: `a23588c8696989cba0e0283454cfd175a9ab1e03`
- Scope: repository ownership, stable and experimental surfaces, and integration boundaries
- Evidence: `src/backtest_sanity/__init__.py`, `src/strategy_lab/cli.py`, and `tests/`
- Residual risks: dynamic producer behavior remains outside this repository.
- Next gate: version cross-repository artifacts without importing producer runtime ownership.

## Ownership

`honest-backtest` owns skeptical validation methods and synthetic teaching
examples. It is an independent module in the Trading Portfolio, not a second
trading system and not a child process of `trading-bot-v2`.

```text
producer repository
  -> public-safe candidate artifact
  -> backtest_sanity deterministic rejection checks
  -> bounded validation verdict
  -> producer-owned paper/forward observation

strategy_lab (experimental, separate package)
  -> private inventory / registry / queue / advisory proposal
  -> deterministic validation must still reject or defer

orders, accounts, recipients, runtime ownership
  -> outside this repository
```

## Stable Surface

The symbols exported by `backtest_sanity.__all__` are the public API. They cover
data checks, time-aware splits, significance and multiplicity, costs,
robustness, forward logging, named anti-overfitting statistics, and injected
adversarial reviewers. Detailed statistical assumptions remain in
[`docs/architecture.md`](docs/architecture.md) and the API reference.

## Experimental Surface

`strategy_lab` is independently importable and tested, but its file schemas and
CLI are experimental. Its commands can inventory explicitly supplied roots,
maintain bounded registry/queue artifacts, estimate advisory work, or create a
draft proposal. It cannot change `backtest_sanity` verdicts or grant authority.

## Cross-Repository Boundary

The bridge is artifact-based. `trading-bot-v2` owns candidate production,
private data, paper lifecycle, and operational decisions. `honest-backtest`
owns validation semantics. Neither repository inherits authority from the
other. Unknown schema versions, statuses, or incomplete trial provenance must
fail closed.

## Evidence Ceiling

A passing check means only that the supplied claim was not rejected by that
specific method under its declared assumptions. Untouched forward evidence
remains necessary, and even that does not grant execution authority.
