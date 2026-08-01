# Documentation Index

Status: **CURRENT**

- Verified: 2026-08-01
- Verified against: `0f537a8fa0b80b17d100d38c0696f9a07d8e4ba6`
- Scope: reading order and stable/experimental documentation ownership
- Evidence: [documentation contract validator](../scripts/check_portfolio_docs.py)
- Residual risks: experimental schemas may change before a stable release.
- Next gate: keep every current page tied to code, tests, and the local portfolio projection.

`honest-backtest` is a validation toolkit, not a trading system or a
profitability claim.

## Read Order

1. [Repository README](../README.md): scope, examples, and limitations.
2. [Current State](../CURRENT_STATE.md): verified capabilities and evidence ceilings.
3. [Repository Architecture](../ARCHITECTURE.md): ownership and integration boundaries.
4. [Current Roadmap](../ROADMAP.md): completed/current/next/later gates.
5. [Trading Portfolio Projection](trading-portfolio-roadmap.md): bounded cross-repository role.
6. [Project Map](project-map.md): source/module map and non-claims.
7. [Validation Architecture](architecture.md): seven validation layers.
8. [Public API](api-reference.md): supported `backtest_sanity` surface.
9. [Strategy Lab Experimental API](strategy-lab-experimental.md): local/private
   inventory, registry, queue, and guarded advisory tooling.
10. [Validation Bridge Contract](validation-bridge-contract.md): public-safe
    candidate, verdict, and forward-evidence boundary.

## Stable And Experimental Surfaces

| Surface | Status | Contract |
|---|---|---|
| `backtest_sanity` exports | stable public API | Small pure validation functions and `ForwardLog`; see `api-reference.md`. |
| `examples/01..09` | stable teaching examples | Synthetic, deterministic demonstrations. |
| `strategy_lab` package and CLI | experimental | File-based private research sandbox; schemas may change. |
| External model provider | explicit opt-in experimental | Advisory only; requires separate environment and cost gates. |

## Related Documents

- [Assumptions and overfitting statistics](overfitting-statistics.md)
- [Use cases and residual risk](use-cases.md)
- [Strategy Lab storage](strategy-lab-storage.md)
- [Strategy Lab data model](strategy-lab-data-model.md)
- [Strategy Lab runtime](strategy-lab-runtime.md)
- [Strategy Lab LLM loop](strategy-lab-llm-loop.md)
- [Historical Strategy Lab phase plan](history/strategy-lab-roadmap.md)

## Integration Boundary

The sibling `trading-bot-v2` project may submit a public-safe candidate artifact
through its own validation bridge. This repository never receives exchange
credentials, private trade rows, candidate rankings, runtime ownership, or
execution authority. A generic validation pass means only `needs_forward`. A
producer may map a complete hard-validation result to `PAPER_FORWARD_READY`
under the public contract; that still permits only paper/forward observation.
