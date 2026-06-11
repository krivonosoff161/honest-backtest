# Strategy Lab Storage

## Rule

Repository files contain code, documentation, examples, and tiny synthetic
fixtures. Heavy local research data lives outside the repository.

Private deployments should choose an external data root outside this
repository. The public project should not publish real local paths, real
symbols, private signal logs, or experiment results.

## Public vs private boundary

| Location | Allowed content |
|---|---|
| Public repository | Code, documentation, synthetic examples, schemas, empty fixtures. |
| Private research workspace | Real manifests, raw-data inventories, experiment results, filter findings, dashboards, and notes. |

The public repository explains how the lab works. It must not expose which
filters, symbols, regimes, or parameter sets performed well in private
research.

## Source categories

A private deployment can inventory these source categories:

| Source category | Notes |
|---|---|
| Raw tick tape | Per-symbol trade files with timestamp, received timestamp, side, price, size, and trade id. |
| Feature logs | Per-timeframe feature files derived from market data. |
| Signal journals | Historical paper decisions and outcomes. |
| Event journals | News, event, or scanner-style research logs. |
| Historical archives | Prior runs, charts, labels, and research notes. |
| Old research scripts | One-off hunts and reports that should be indexed before reuse. |
| Old backtest outputs | Sweep outputs and summaries. |

These sources are inputs for a manifest, not dependencies that should be copied
into this repository.

## Proposed external directory layout

```text
<private-research-root>\
  raw\
    ticks\
    ohlcv\
    external\
  features\
  experiments\
    queue\
    running\
    completed\
    failed\
  results\
    trades\
    metrics\
    candidates\
  registry\
  graph\
  obsidian-vault\
  grafana\
  reports\
  cache\
  manifests\
```

## Environment variables

```text
STRATEGY_LAB_DATA_DIR=<private-research-root>
STRATEGY_LAB_TICK_DIR=<private-tick-root>
STRATEGY_LAB_MAX_WORKERS=4
STRATEGY_LAB_MAX_RUNTIME_MIN=60
STRATEGY_LAB_LLM_ENABLED=false
```

The values above are examples for a private deployment. The public package
must not require those variables for import or tests.

## Data management rules

- Never commit raw ticks, live logs, secrets, or private reports.
- Store append-only experiment records before aggregate reports.
- Every derived dataset needs a manifest with source paths, date range,
  symbols, schema version, and generation command.
- Every experiment result needs a deterministic `experiment_id`.
- If a source row cannot be parsed, record a rejected row count instead of
  silently skipping it.
- If heavy data is moved, update the manifest rather than hard-coding a new
  path in strategy logic.

## First manifest fields

```json
{
  "schema_version": 1,
  "source_id": "tick_tape",
  "source_path": "<private-source-root>",
  "format": "csv_or_csv_gz",
  "symbols": ["SYNTH-A"],
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "row_count": 0,
  "byte_count": 0,
  "fields": ["ts_ms", "recv_ts_ms", "symbol", "side", "price", "size", "trade_id"],
  "created_at": "UTC timestamp",
  "notes": "read-only inventory result"
}
```

The first implementation task should be an inventory command that builds this
manifest without modifying source data.
