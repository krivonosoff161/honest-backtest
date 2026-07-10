# Strategy Lab Experimental Interface

Status: **EXPERIMENTAL**. This package is shipped, importable, and tested, but
its file schemas and CLI are not stable API guarantees.

Strategy Lab is a local/private hypothesis-management sandbox around the stable
`backtest_sanity` validation core. It does not run strategies, connect to an
exchange, place orders, or make a candidate profitable.

## Commands

| Command | Network | Writes | Purpose |
|---|---|---|---|
| `inventory` | no | private manifests/reports | Read-only inventory of configured local sources. |
| `registry-init` | no | private registry layout | Creates private registry and queue directories. |
| `registry-add` | no | private registry JSON/JSONL | Validates a bounded research record. |
| `queue-plan` | no | private queue JSON/JSONL | Validates and queues an experiment plan. |
| `llm-estimate` | no | no | Estimates a guarded LLM request. |
| `llm-doctor` | no | no | Reports local provider configuration without calling it. |
| `llm-plan` | opt-in | private proposal/cost artifacts | Produces a guarded research proposal; live provider calls require explicit cost and environment switches. |

## Schema Rules

All accepted registry and experiment records use `schema_version: 1`. The
registry permits only `draft`, `tested`, `rejected`, `weak`, `needs_forward`,
and `research_note`. Terms such as `approved`, `profitable`, `ready`, `live`,
and `trade` are rejected.

Experiment plans require bounded variants and runtime. LLM calls are forbidden
inside deterministic experiment plans. Any LLM proposal remains a draft until a
separate deterministic runner and validation process evaluate it.

## Storage Rule

`--out-dir` must be private and outside the source tree being inventoried. Do
not commit manifests, inventories, proposals, cost ledgers, raw provider
responses, market data, or strategy findings to this public repository.

## Cost Rule

The default provider is a deterministic stub. A live Alibaba provider requires:

```text
--live
--i-accept-cost
STRATEGY_LAB_LLM_ENABLED=true
provider API-key environment variable
```

Call, token, run-cost, and UTC daily-cost budgets are checked before a request.
The daily limit reads the current day's cost ledger only.
