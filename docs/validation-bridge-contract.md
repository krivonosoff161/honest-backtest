# Validation Bridge Contract

Status: **REFERENCE CONTRACT**. Version: `1.0.0`.

This document describes the public-safe boundary between a candidate-producing
research workbench and the `backtest_sanity` validation methods. It does not
ship an exchange integration, strategy edge, private candidate rows, or order
authority.

## Candidate Input

A candidate must have a stable candidate ID, source-run provenance, symbol and
timeframe identifiers, strategy identifier, declared parameters/filters, fee
and slippage assumptions, deterministic metrics, simulated trade returns, data
window metadata, and a schema version.

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

The strongest positive status is `PAPER_FORWARD_READY`. It means the candidate
may be observed in a paper/forward process under the producer's own controls.
It does not mean profitable, approved, live-ready, or authorized to place an
order.

## Status Vocabulary

```text
HARD_REJECT | FAILED_OVERFIT | FAILED_COSTS | FAILED_FRAGILITY
FAILED_OOS | FAILED_DATA_QUALITY | REGIME_ONLY | NEEDS_MORE_DATA
PAPER_FORWARD_READY
```

Unknown schema versions or unrecognized statuses must be rejected by an
integration, not silently interpreted as a pass.

## Forward Evidence

Forward evidence should link the decision ID, candidate ID, decision time,
outcome time, cost model, and idempotency/lineage identifier. `ForwardLog` is
a small local JSONL helper, not a tamper-evident ledger; stronger systems need
their own hash, signing, locking, or immutable-store controls.

## Non-Authority Rule

No candidate, report, forward row, LLM proposal, or bridge status authorizes
execution. Live order policy belongs outside this repository and outside this
contract.
