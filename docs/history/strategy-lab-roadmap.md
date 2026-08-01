# Historical Strategy Lab Roadmap

Status: **HISTORICAL / SUPERSEDED**

- Preserved: 2026-08-01
- Originally verified against: earlier repository phases; not current authority
- Superseded by: [`../../ROADMAP.md`](../../ROADMAP.md)
- Scope: original phased design intent for Strategy Lab
- Residual risks: several early phases are implemented while later phases remain ideas.
- Load policy: planning evidence only; verify every claim against current code and tests.

This document preserves the original phase sequence. It must not be used as the
current repository roadmap or as authority to run private data, model, or
execution work.

## Original Phase 0 - Foundation

- Document the experimental discovery boundary.
- Define external storage, records, and read-only inventory.
- Keep `backtest_sanity` as the skeptical validation core.

## Original Phase 1 - Inventory

The plan introduced a read-only inventory command for explicitly configured
research roots, with manifests and reports written outside those roots. That
bounded inventory command is now implemented and tested.

## Original Phase 2 - Synthetic Strategy Lab

The plan proposed deterministic synthetic strategies, simulation with costs,
and offline tests. Pieces exist across the current repositories, but this broad
phase is not a single stable `honest-backtest` product surface.

## Original Phase 3 - Local Data Adapter

The plan proposed manifest-driven local adapters and external caches. Private
adoption and real datasets remain outside this public repository.

## Original Phase 4 - Strategy Hypothesis Zoo

The plan proposed bounded trend, breakout, mean-reversion, flow, volatility,
and high-volatility families. These are not a current public capability claim.

## Original Phase 5 - Candidate Filter And Validation Gauntlet

The skeptical validation core exists. Producer-specific filtering, full trial
provenance, and promotion remain cross-repository concerns. The strongest
positive ceiling is paper/forward observation.

## Original Phase 6 - Registry And Graph

Bounded registry and queue records are implemented in the experimental package.
Graph exports are not a stable public validator surface.

## Original Phase 7 - Dashboards

Read-only dashboard ideas were planned but are not part of the stable validator.

## Original Phase 8 - LLM Research Loop

A guarded experimental advisory path exists, including deterministic stub and
budget checks. Model output remains draft evidence and cannot alter validation
or authority.

## Original Phase 9 - Forward/Paper Evidence

The stable toolkit includes `ForwardLog`, and the bridge defines a paper-only
positive ceiling. A tamper-evident operational paper ledger belongs to the
producer, not this repository.

## Preserved Release Rule

No phase introduces live order placement. Any future execution system requires
a separate project boundary, approval, and risk model.
