# Strategy Lab Roadmap

## Phase 0 - Foundation

- Document the lab boundary: experimental discovery layer, not live trading.
- Define storage layout and local data root.
- Define experiment, result, candidate, and registry records.
- Inventory existing local data and old research outputs.
- Keep `backtest_sanity` unchanged as the validation core.

## Phase 1 - Inventory

Build a read-only inventory command that scans configured roots:

- tick tape;
- feature logs;
- signal journals;
- scout journals;
- archives;
- old backtest outputs;
- old research reports.

Output:

```text
manifests/data_sources.json
reports/inventory_summary.md
```

No source file mutation.

Initial command shape:

```bash
python -m strategy_lab.cli inventory \
  --source-root <read-only-research-source> \
  --tick-root <optional-read-only-tick-root> \
  --out-dir <private-research-output>
```

The output directory must be outside the scanned source roots.

## Phase 2 - Synthetic strategy lab

- Implement a tiny strategy-lab package with synthetic data only.
- Add 3-5 simple strategies.
- Add paper simulation with fees and slippage.
- Produce deterministic reports.
- Tests must run without network and without LLMs.

## Phase 3 - Local data adapter

- Read local OHLCV/feature/tick-derived data from manifests.
- Do not hard-code workstation paths in strategy code.
- Add small fixture extracts for tests only.
- Cache derived candles/features under the external lab root.

## Phase 4 - Strategy hypothesis zoo

Add bounded families:

- trend;
- breakout;
- mean reversion;
- volume/flow;
- volatility;
- high-volatility alt/meme patterns.

Every strategy must declare supported timeframes and parameter schema.

## Phase 5 - Candidate filter and validation gauntlet

- Filter obvious noise before expensive validation.
- Apply costs, splits, significance, and robustness checks.
- Record rejection reasons.
- Promote only to `needs_forward`; stronger conclusions belong in private
  research notes and still do not imply execution permission.

## Phase 6 - Registry and graph

- Store candidates and lineage in SQLite/JSONL.
- Export graph JSON/GraphML.
- Export Obsidian notes for strategies, filters, regimes, and findings.

## Phase 7 - Dashboards

- Export aggregated tables for Grafana.
- Track runtime, candidate counts, rejection reasons, and family performance.
- Keep dashboards read-only.

## Phase 8 - LLM research loop

- Add provider-neutral LLM adapters.
- Cheap model: summaries.
- Medium model: next experiment plans.
- Strong model: adversarial review.
- Enforce cost and runtime budgets.

## Phase 9 - Forward/paper evidence

- Append-only forward queue.
- Time-boxed paper outcomes.
- Registry status upgrades only from forward evidence.

## Release rule

No phase may introduce live order placement. Any future execution system must
be a separate project with a separate approval and risk model.
