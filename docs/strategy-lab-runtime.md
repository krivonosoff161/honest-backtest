# Strategy Lab Runtime

## Local runtime model

The lab is intended to run on a local workstation first. It should be able to
pause, resume, and inspect progress without relying on cloud infrastructure.

```text
planner
  -> experiment queue
  -> worker pool
  -> simulator
  -> metrics reducer
  -> validation gauntlet
  -> registry update
  -> reports / dashboards / notes
```

## Queues

Use append-only or transactional records for:

| Queue | Purpose |
|---|---|
| `experiments/queue` | Accepted plans waiting to run. |
| `experiments/running` | Plans currently claimed by a worker. |
| `experiments/completed` | Plans that produced metrics and reports. |
| `experiments/failed` | Plans that crashed, timed out, or produced invalid data. |

SQLite can be used for coordination once the file-based contract is stable.

The first file-based implementation exposes these commands:

```bash
python -m strategy_lab.cli registry-init --out-dir <private-research-output>
python -m strategy_lab.cli queue-plan --plan <experiment-plan.json> --out-dir <private-research-output>
python -m strategy_lab.cli registry-add --entry <registry-entry.json> --out-dir <private-research-output>
```

`queue-plan` validates that every experiment has bounded runtime and variant
budgets before writing `experiments/queue/<experiment_id>.json` and appending a
small queue index row. `registry-add` writes immutable registry records under
`registry/` and appends `registry/registry_entries.jsonl`.

The registry status vocabulary is intentionally conservative:

```text
draft
tested
rejected
weak
needs_forward
research_note
```

It does not include approval, profitability, readiness, or live-trading
statuses.

## Budgets

Every plan needs explicit budgets:

```json
{
  "max_variants": 1000,
  "max_runtime_seconds": 900,
  "max_symbols": 30,
  "max_timeframes": 3,
  "stop_if_bad_after": 100,
  "llm_enabled": false,
  "llm_max_cost_rub": 0.0
}
```

The runner should stop early when a strategy family is clearly poor under the
current gate. This prevents one bad family from consuming the whole machine.

## Early stopping examples

- no trades after enough bars;
- spam rate above threshold;
- median MFE <= median MAE for the first N variants;
- net result fails costs across all early variants;
- parser/data coverage below minimum;
- runtime budget exceeded.

Early stopping must be recorded as evidence, not treated as a silent skip.

## Worker safety

- No order placement modules.
- No exchange private endpoints.
- No mutation of source tick archives.
- No rewriting append-only experiment or forward logs.
- No LLM calls inside deterministic unit tests.
- No network dependency for core tests.

## Reports

Each completed experiment should write:

```text
summary.md
plan.json
metrics.csv
metrics.json
trades_sample.csv
candidate_refs.json
validation.json
```

Large trade-level outputs can be stored as Parquet later, but the first
version should keep simple CSV/JSON for inspection.

## Grafana boundary

Grafana should read aggregated tables only:

- experiment counts;
- runtime;
- candidate statuses;
- family-level metrics;
- asset-cluster metrics;
- validation failures;
- cost and slippage sensitivity.

Grafana should not be the source of truth.

## Obsidian boundary

Obsidian exports are derived notes:

```text
obsidian-vault/
  strategies/
  filters/
  regimes/
  assets/
  findings/
  daily/
```

Notes should link back to `experiment_id` and `registry_id`. They should not
replace structured data.
