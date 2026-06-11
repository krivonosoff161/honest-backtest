# Strategy Lab LLM Loop

## Role of LLMs

LLMs are research coordinators, not calculation engines. The code computes
signals, fills, fees, MFE, MAE, drawdowns, splits, and robustness. LLMs read
summaries and propose the next bounded experiments.

## Model tiers

| Tier | Role | Example work |
|---|---|---|
| Cheap | Batch summarization | Summarize failed families, group similar rejects, draft notes. |
| Medium | Hypothesis planning | Propose filter combinations and next parameter grids. |
| Strong | Skeptical review | Try to refute strong candidates and identify overfit risks. |

The strong model should be called only after deterministic metrics justify it.

## Inputs to LLMs

Give LLMs compressed evidence:

- top/bottom candidate tables;
- family-level aggregates;
- validation failures;
- graph neighborhoods;
- previous hypothesis notes;
- runtime and cost budgets;
- explicit constraints.

Do not send:

- raw tick files;
- secrets;
- private account data;
- millions of trade rows;
- unbounded logs.

## Output contract

LLM experiment proposals should be machine-readable:

```json
{
  "hypothesis": "VWAP reclaim may improve volume breakout quality on a synthetic high-volatility cluster.",
  "risk_of_overfit": "High if only one asset or one day supports it.",
  "next_experiments": [
    {
      "strategy_id": "volume_breakout",
      "asset_cluster": "synthetic_high_vol",
      "timeframes": ["5m", "15m"],
      "filters": {
        "vwap_reclaim": [true],
        "benchmark_regime": ["not_down", "up_or_flat"]
      },
      "budgets": {
        "max_variants": 300,
        "max_runtime_seconds": 600
      },
      "stop_condition": "Reject if median MFE/MAE <= 1.1 after first 100 variants."
    }
  ]
}
```

## Guardrails against overfitting

- The LLM cannot change validation thresholds after seeing a result unless it
  creates a new experiment lineage.
- Every hypothesis needs a train/validation/forward boundary.
- Parameter grids must be bounded before the run starts.
- Candidate promotion requires deterministic checks, not prose.
- Adversarial review should default to `rejected` when evidence is thin.
- LLM proposals are untrusted inputs: validate schema, budgets, and allowed
  fields before writing any queue record.
- LLM output cannot directly mutate registry status, validation thresholds, or
  gauntlet gates.
- Registry updates require deterministic reruns plus human or automated policy
  approval.

## Local provider integration

The lab should use provider adapters rather than hard-coded SDK calls:

```text
LLMProvider
  -> summarize_batch(input) -> summary
  -> propose_experiments(input) -> ExperimentPlan[]
  -> review_candidate(input) -> verdict
```

This allows local or cloud providers to be swapped later without changing the
research engine.

Training or fine-tuning a custom model should wait until the registry contains
enough high-quality experiment/outcome pairs. Before that, retrieval over the
registry and Obsidian notes is cheaper and safer.
