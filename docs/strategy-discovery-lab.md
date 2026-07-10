# Strategy Discovery Lab

Status: **EXPERIMENTAL / SHIPPED**. The package and CLI are importable and
tested, but the schema and local-workflow details may change.

## Purpose

The Strategy Discovery Lab is an experimental local sandbox for generating,
logging, and triaging strategy hypotheses before they enter the existing
seven-layer validation gauntlet.

It is not part of the stable `backtest_sanity` API yet. It should be treated
as a quarantined research layer:

```text
strategy discovery generates candidates
backtest_sanity tries to reject them
forward logging decides whether they deserve more attention
```

The lab's useful output is not a finished trading setup. Its useful output is a
structured candidate record with enough evidence to decide what should be
tested harder.

## Statistical gates

Because the lab produces candidates by the batch, it is exactly the setting
the named overfitting statistics were built for. The lab records every
variant tried; the validation layer then applies PBO (CSCV) to the full sweep
matrix, DSR against the full trial list, and PSR/MinTRL to the surviving
track record. Only candidates that pass these gates move to `needs_forward`.
Passing grants forward-paper attention, never live permission, and no private
results appear in this repository. See
[Named overfitting statistics](overfitting-statistics.md).

## Related docs

- [Storage](strategy-lab-storage.md)
- [Data model](strategy-lab-data-model.md)
- [Runtime](strategy-lab-runtime.md)
- [LLM loop](strategy-lab-llm-loop.md)
- [Roadmap](strategy-lab-roadmap.md)
- [Core validation architecture](architecture.md)

## Non-goals

- No live trading.
- No broker or exchange order placement.
- No real market data committed to this repository.
- No claim that a candidate is profitable.
- No hidden optimization until a pretty result appears.
- No LLM calculating candle metrics, fees, MFE, MAE, or PnL by hand.
- No change to the seven-layer validation architecture.

## Pipeline

```text
local market data
  -> experiment planner
  -> strategy hypothesis zoo
  -> batch simulator
  -> candidate filter
  -> honest validation gauntlet
  -> forward/paper queue
  -> strategy registry
  -> graph / dashboards / research notes
  -> LLM research loop
```

The correct interpretation of a surviving historical candidate is:

> This candidate was not rejected under the current tests and needs forward
> evidence.

It is not:

> This works.

## Components

| Component | Responsibility |
|---|---|
| Data store | Local OHLCV, ticks, feature snapshots, manifests, and cached derived data. |
| Experiment planner | Builds bounded experiment batches from strategy families, filters, assets, regimes, and budgets. |
| Strategy hypothesis zoo | Deterministic strategy candidates with explicit parameters and supported timeframes. |
| Batch simulator | Runs paper-only entries/exits, fees, slippage, stops, targets, and time stops. |
| Candidate filter | Drops obvious noise before expensive validation or LLM analysis. |
| Validation gauntlet | Applies data integrity, splits, costs, significance, robustness, forward logging, and adversarial review. |
| Registry | Stores candidates, statuses, evidence, failure modes, and experiment lineage. |
| Graph layer | Links strategy -> filter -> asset cluster -> timeframe -> market regime -> result. |
| Grafana layer | Displays operational and research metrics from aggregate tables. |
| Obsidian layer | Exports human-readable research notes and wiki-style links. |
| LLM research loop | Reads summaries and graph neighborhoods, proposes next experiments, and reviews strong candidates. |

## Candidate lifecycle

```text
hypothesis
  -> simulated
  -> filtered
  -> validating
  -> rejected | weak | needs_forward | research_note
```

| Status | Meaning |
|---|---|
| `rejected` | Failed a hard check: data leak, costs, fragile split, bad robustness, or obvious noise. |
| `weak` | Some signal exists, but it is unstable, too sparse, or too sensitive. |
| `needs_forward` | Historical checks did not reject it; append-only forward evidence is required. |
| `research_note` | A private note worth studying later; it carries no execution or recommendation meaning. |

No status in this lifecycle grants live trading permission.

## First MVP boundary

The first implementation should be deliberately small:

- synthetic and local-file data only;
- 5-10 hypothesis families;
- 10-30 assets;
- 3 timeframes;
- explicit fees and slippage;
- deterministic reports in JSON/CSV/Markdown;
- no network required for tests;
- no LLM required for tests.

The first good report should look like:

```text
volume breakout + liquidity filter + benchmark regime filter
looked better on synthetic high-volatility assets at 5m than on synthetic majors at 1m,
but failed robustness on the validation split.
```

That is more valuable than a single leaderboard.
