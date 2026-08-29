# Validation Bridge Contract

Status: **REFERENCE CONTRACT**. Upstream version: `1.3.0`.

- Canonical owner: `trading-bot-v2`
- Validator-method owner: `honest-backtest`
- Pinned upstream source: [`5e5966fe143de26ac975fd86efc473345eb0dbba`](https://github.com/krivonosoff161/trading-bot-v2/blob/5e5966fe143de26ac975fd86efc473345eb0dbba/docs/validation-bridge-contract.md)
- Authority: `none`

This is a deliberately bounded public projection of the canonical producer-side
contract. `trading-bot-v2` owns candidate schemas, generation publication,
paper lifecycle, and later delivery. `honest-backtest` owns the generic
skeptical validation methods it exposes. This document does not ship an exchange
integration, strategy edge, private candidate rows, runtime state, or order
authority.

## Candidate Input

A candidate must have a stable candidate ID, source-run provenance, symbol and
timeframe identifiers, strategy identifier, declared parameters/filters, fee
and slippage assumptions, deterministic metrics, simulated trade returns, data
window metadata, a schema version, and the exact generation/evidence identities
required by the canonical source.

The producer must record the complete trial set or trial count used to select
the candidate. Validation cannot honestly correct multiple testing if it only
sees the winning variant.

## Validation Output

The validator returns a structured report containing:

- candidate and source-run IDs;
- gate-by-gate check results and messages;
- failed checks and reason codes;
- a hard status;
- contract version and timestamp.

The strongest positive status is `PAPER_FORWARD_READY`. It means only that the
candidate was **not rejected by the defined checks** and may be considered for a
separately controlled paper/forward observation path under the producer's own
controls. It does not mean profitable, approved, live-ready, or authorized to
place an order.

## Status Vocabulary

```text
HARD_REJECT | FAILED_OVERFIT | FAILED_COSTS | FAILED_FRAGILITY
FAILED_OOS | FAILED_DATA_QUALITY | REGIME_ONLY | NEEDS_MORE_DATA
PAPER_FORWARD_READY
```

Unknown schema versions, unrecognized statuses, missing generation bindings, or
incomplete/tampered evidence must be rejected by an integration, not silently
interpreted as a pass.

## Forward Evidence

Forward evidence should link the decision ID, candidate ID, decision time,
outcome time, cost model, and idempotency/lineage identifier. `ForwardLog` is
a small local JSONL helper, not a tamper-evident ledger; stronger systems need
their own hash, signing, locking, or immutable-store controls.

## Non-Authority Rule

No candidate, report, forward row, LLM proposal, or bridge status authorizes
execution. Live order policy belongs outside this repository and outside this
contract.

## Projection Update Rule

`trading-portfolio-roadmap.yaml` records the upstream schema version, exact
commit, and canonical UTF-8/LF SHA-256. Any change to those fields needs an
explicit projection update. CI verifies both the content hash and the
checked-out upstream Git HEAD; a matching digest does not prove runtime
correctness or statistical quality.
