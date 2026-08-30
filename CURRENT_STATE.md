# Current State

Status: **CURRENT**

- Verified: 2026-08-30
- Verified against: `a392333caf0d74d39fbb502b3aef98a0e51b5b9d`
- Scope: current public capabilities and evidence ceilings
- Evidence: `src/backtest_sanity`, `src/strategy_lab`, and 75 collected test functions
- Residual risks: deterministic synthetic checks do not prove performance on
  dependent market data or untouched future observations.
- Next gate: keep the validation bridge and Trading Portfolio projection aligned
  while adding time-series-aware methods only with focused evidence.

## Implemented

- `backtest_sanity` exposes seven small validation layers plus PSR, DSR,
  minimum track-record length, and PBO/CSCV statistics.
- Nine deterministic synthetic examples demonstrate known failure modes.
- `ForwardLog` provides a basic append-only local JSONL helper. It is not a
  tamper-evident ledger or execution simulator.
- The public validation bridge defines bounded input/output semantics. Its
  strongest positive result permits only paper/forward observation.
- The separate experimental `strategy_lab` package implements inventory,
  registry, queue, cost-estimate, environment-diagnostic, and guarded proposal
  commands. It is not part of the stable validator API.

## Implemented With Boundaries

- Statistical resampling assumes independent observations where documented;
  it can reject weak claims but cannot certify a trading edge.
- Strategy Lab uses local/private output roots and can make an external model
  call only through explicit experimental switches. That path is advisory and
  is not required by the deterministic validator.
- Cross-repository integration is a public-safe artifact contract. This
  repository does not read the producer's runtime database, private strategy
  parameters, rankings, credentials, recipients, or account data.

## Not Implemented Or Not Claimed

- No backtesting engine, market-data loader, broker integration, order path,
  runtime supervisor, or trading authority.
- No proof of profitability, safety, live readiness, or current provider
  availability.
- No complete time-series-aware treatment for every dependence structure.
- No automatic promotion from validation output to execution.

The machine-readable local portfolio projection is
[`docs/trading-portfolio-roadmap.yaml`](docs/trading-portfolio-roadmap.yaml).
