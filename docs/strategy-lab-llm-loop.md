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
  "schema_version": 1,
  "proposal_type": "strategy_research_plan",
  "status": "draft",
  "hypotheses": [
    {
      "id": "vwap_reclaim_volume_breakout_001",
      "asset_group": "synthetic_high_vol",
      "strategy_family": "volume_breakout",
      "filters": ["vwap_reclaim", "benchmark_regime_not_down"],
      "next_action": "Run a bounded offline batch and reject if validation metrics stay weak.",
      "safety_note": "Offline research only; no live execution and no private paths in the proposal."
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

## Alibaba Model Studio setup

The experimental Alibaba provider uses Model Studio's OpenAI-compatible chat
endpoint. Local setup is intentionally explicit:

```text
DASHSCOPE_API_KEY=<region-specific-api-key>
STRATEGY_LAB_LLM_ENABLED=true
DASHSCOPE_REGION=singapore|us|beijing|hong_kong
```

Alternatively, set `DASHSCOPE_BASE_URL` or pass `--base-url` directly when a
workspace uses a custom endpoint. API keys and base URLs are region-specific;
do not mix a Beijing key with a Singapore or US endpoint.

Inspect local configuration without sending a request:

```bash
python -m strategy_lab.cli llm-doctor
```

Run a dry budget estimate before any live call:

```bash
python -m strategy_lab.cli llm-estimate \
  --inventory-latest <private-research-output>/manifests/inventory_latest.json \
  --out-dir <private-research-output> \
  --provider alibaba \
  --model qwen3.5-flash
```

Live calls require all guard switches:

```bash
python -m strategy_lab.cli llm-plan \
  --inventory-latest <private-research-output>/manifests/inventory_latest.json \
  --out-dir <private-research-output> \
  --provider alibaba \
  --model qwen3.5-flash \
  --live \
  --i-accept-cost
```

Training or fine-tuning a custom model should wait until the registry contains
enough high-quality experiment/outcome pairs. Before that, retrieval over the
registry and Obsidian notes is cheaper and safer.
