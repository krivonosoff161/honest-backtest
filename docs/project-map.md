# Project map — for reviewers and maintainers

## What it does

`backtest_sanity` is a set of small, pure validation functions arranged in
seven layers, each catching one class of backtest self-deception: look-ahead,
in-sample tuning, luck, costs, parameter overfitting, missing forward proof,
and single-pass rationalization. It wraps around any backtesting engine — it
is **not** one itself.

The honest output of the full stack is never "this works"; it is *"this is
not yet falsified — now run it forward."* (See
[architecture.md](architecture.md) for the layer-by-layer rationale.)

## Mental model

```
result you want to believe
  -> 1 data_checks    look-ahead / order / survivorship
  -> 2 splits         holdout · walk-forward · purged k-fold
  -> 3 significance   bootstrap CI · permutation · Bonferroni/BH
  -> 4 costs          gross vs net
  -> 5 robustness     parameter plateau · sub-period stability
  -> 6 forward        append-only decision/outcome log
  -> 7 adversarial    a panel tries to REFUTE the claim
  => "not obviously broken"  (≠ true)
```

## Key modules

| File | Layer | Public functions | Size |
|---|---|---|---|
| `data_checks.py` | 1 | `lookahead_correlation`, `timestamp_monotonic`, `survivorship_note` | ~30 lines |
| `splits.py` | 2 | `holdout`, `walk_forward`, `purged_kfold` | ~40 lines |
| `significance.py` | 3 | `bootstrap_ci`, `permutation_test` (bias-corrected p), `bonferroni`, `benjamini_hochberg` | ~65 lines |
| `costs.py` | 4 | `apply_costs` | ~25 lines |
| `robustness.py` | 5 | `param_sweep`, `subperiod_stability` | ~35 lines |
| `forward.py` | 6 | `ForwardLog` (append-only JSONL) | ~35 lines |
| `adversarial.py` | 7 | `adversarial_review` (inject `verify(claim) -> bool` callables) | ~35 lines |
| `_synth.py` | — | synthetic data for examples/tests; **no real market data anywhere** | ~20 lines |

Everything takes arrays/lists in and returns dicts/scalars out; no classes
except `ForwardLog`, no global state, numpy is the only dependency.

## What exists today

- All seven layers implemented, each with tests (16 total) and a worked
  example (`examples/01..07`, all on synthetic data, no keys).
- Deterministic, seeded examples — outputs are reproducible.

## What is NOT included (by design)

- No backtesting engine, data loaders, broker/exchange code, or strategy code.
- No built-in LLM verifiers — layer 7 takes injected callables (pair with
  [llm-router](https://github.com/krivonosoff161/llm-router) or use
  deterministic fakes).
- No time-series-aware resampling: bootstrap/permutation assume i.i.d.
  observations (documented in `significance.py`); block bootstrap is out of
  scope today.
- No claim of profitability, anywhere.

## Planned experimental layer

The repository may grow a separate Strategy Discovery Lab, documented in
[strategy-discovery-lab.md](strategy-discovery-lab.md). That layer is allowed
to generate strategy hypotheses only if it preserves the core boundary:

```text
discovery is experimental
validation remains skeptical
live trading stays out of scope
```

In other words, the lab may generate candidates; `backtest_sanity` tries to
falsify them. A candidate that survives historical tests is still only
`needs_forward` until append-only forward evidence exists.

## How to inspect without reading every line

1. Read [architecture.md](architecture.md) — the whole design in one page.
2. Run the examples in order (`01` → `07`): each prints the failure it catches
   and a one-line lesson. See [examples/README.md](../examples/README.md).
3. Skim `tests/test_backtest_sanity.py` names — one or more per layer.

## How to run checks

```bash
python -m pytest -q          # full offline suite
python -m ruff check .
python examples/01_lookahead_mirage.py    # ... through 07
```

CI runs pytest and ruff on Python 3.9 / 3.11 / 3.12.

## How to extend safely

- New check: add a pure function to the matching layer module + a test + (if
  it teaches a failure mode) a small synthetic example. Keep the
  arrays-in/dict-out convention.
- New layer: only if it catches a *distinct class* of self-deception not
  covered above; update `architecture.md` and the README table together.
- Do not add real market data, paid APIs, or a strategy — that breaks the
  repo's core promise ("the value is the method, not an edge").

## Reviewer checklist (for future changes, incl. agent-generated)

- [ ] No real market data, tickers-with-numbers, or implied profitability.
- [ ] New statistics state their assumptions (i.i.d.? stationarity?) in the docstring.
- [ ] Every example stays deterministic (seeded) and runs with numpy only.
- [ ] README layer table, `architecture.md` and `__init__.py` exports stay in sync.
- [ ] p-value code avoids the p=0 trap (bias-corrected formula, cite if changed).
- [ ] The "not a panacea" framing survives any README edit.
- [ ] Experimental discovery docs never imply production suitability or guaranteed profitability.
